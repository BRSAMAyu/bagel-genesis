#!/usr/bin/env python3
"""Mechanical grader for BAGEL Genesis validator evals.

Closes the audit gap: evals/evals.json has 120 evals with prose
`expected_output` and zero fixtures, so no automated harness proved any
validator actually catches what the evals claim. This grader does NOT grade
LLM behavior (that needs live agent runs). It grades the *mechanical
enforcement substrate* that the validator-targeted evals depend on:

  1. POSITIVE: the current skill's own validator suite + lint pass against
     the skill repo (proves the mechanical layer is healthy at this version).
  2. NEGATIVE: for each high-value anti-cheat validator, synthesize a minimal
     fixture embodying the cheat an eval describes, run the validator against
     it, and assert NON-zero exit (the validator must catch the cheat).

A negative test failing means a validator an eval relies on does NOT catch
the documented cheat — a real regression, not a style issue.

Usage:
    python evals/mechanical_grader.py [skill-root]

Exit code: 0 = all graded assertions pass, 1 = at least one failed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SCRIPT_DIR.parent
PY = sys.executable


def run(script: str, root: Path, *, expect_fail: bool) -> tuple[bool, str]:
    """Run a validator script against `root`. Return (matched_expectation, detail)."""
    cmd = [PY, str(SKILL_ROOT / "scripts" / script), str(root)]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    failed = proc.returncode != 0
    matched = failed if expect_fail else (not failed)
    tag = "caught-cheat(non-zero)" if expect_fail else "passed"
    detail = f"exit={proc.returncode} {'OK' if matched else 'MISMATCH'} ({tag})"
    if not matched:
        detail += "\n      output tail: " + "\n      ".join(proc.stdout.splitlines()[-6:])
    return matched, detail


def git_init(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "bagel-test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "bagel-test"], cwd=root, check=True)


def git_commit(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def sha256_text(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def sha256_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extractor_source() -> str:
    return (
        "import re, sys\n"
        "text=open(sys.argv[1], encoding='utf-8').read()\n"
        "m=re.search(r'accuracy:\\s*([0-9.]+)', text)\n"
        "print('recomputed accuracy =', m.group(1))\n"
    )


def write_preregistered_plan(root: Path, public_pem: str | None = None) -> str:
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    extractor = scripts / "extract_metric.py"
    extractor.write_text(extractor_source())
    audit = root / ".bagel/audit"
    audit.mkdir(parents=True, exist_ok=True)
    if public_pem is None:
        public_pem = "-----BEGIN PUBLIC KEY-----\nTEST\n-----END PUBLIC KEY-----\n"
    (audit / "ci-audit-public.pem").write_text(public_pem)
    plan_body = (
        "experiment_plan:\n"
        "  schema_version: research_experiment_plan_v1\n"
        "  study_id: S1\n"
        "  mode: protocol_execution\n"
        "  objective: test CI auditor\n"
        "  hypotheses:\n"
        "    - id: H1\n"
        "      statement: If mechanism then metric improves by 0.1 relative to baseline under test conditions.\n"
        "      falsifiable_metric: accuracy\n"
        "      falsifier: accuracy gain <= 0.01\n"
        "      primary_metric: accuracy\n"
        "      decision_threshold: '> 0.8'\n"
        "      practical_significance_threshold: '>= 0.01'\n"
        "  baselines: [baseline]\n"
        "  controls: [same data]\n"
        "  datasets: [{dataset_id: d1, version_or_hash: h1, split_refs: [s1]}]\n"
        "  seeds: [1, 2, 3]\n"
        "  analysis_plan: {statistical_test: paired_t, correction: none, exclusion_criteria: [], preprocessing_scope: train_only}\n"
        "  stopping_rule: fixed seeds\n"
    )
    (research / "experiment-plan.yaml").write_text(plan_body)
    plan_commit = git_commit(root, "plan")
    (research / "preregistration.yaml").write_text(
        "preregistration:\n"
        "  schema_version: research_preregistration_v1\n"
        "  plan_path: .bagel/research/experiment-plan.yaml\n"
        f"  plan_sha256: {sha256_text(plan_body)}\n"
        f"  plan_commit: {plan_commit}\n"
        f"  audit_public_key_sha256: {sha256_text(public_pem)}\n"
        "  command_pins:\n"
        "    - path: scripts/extract_metric.py\n"
        f"      sha256: {sha256_file(extractor)}\n"
        "  registered_at: '2026-06-18T00:00:00Z'\n"
        "  registered_by: Researcher\n"
        "  approval_ref: TEST-APPROVAL\n"
    )
    git_commit(root, "preregister")
    return plan_commit


def write_metric_artifact(root: Path, value: float = 0.847) -> tuple[Path, str]:
    ev = root / ".bagel/evidence"
    ev.mkdir(parents=True, exist_ok=True)
    metric = ev / "metric.txt"
    metric.write_text(f"accuracy: {value}\n")
    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "extract_metric.py").write_text(extractor_source())
    return metric, sha256_file(metric)


def write_headline_claim(root: Path, evidence_ref: str, extra_metric_values: str = "") -> None:
    research = root / ".bagel/research"
    metric_values = (
        "        - metric: accuracy\n"
        f"          evidence_ref: {evidence_ref}\n"
    ) + extra_metric_values
    (research / "claim-evidence.yaml").write_text(
        "claim_evidence_matrix:\n"
        "  schema_version: research_claim_evidence_v1\n"
        "  claims:\n"
        "    - claim_id: C1\n"
        "      text: metric improved\n"
        "      claim_type: confirmatory\n"
        "      hypothesis_id: H1\n"
        "      metric_refs: [accuracy]\n"
        "      run_refs: [.bagel/evidence/ev-metric.yaml]\n"
        "      ablation_status: complete\n"
        "      reproducibility_status: reproduced\n"
        "      allowed_in_headline: true\n"
        "      metric_values:\n"
        f"{metric_values}"
    )


def fixture_ci_echo_extractor(root: Path) -> None:
    git_init(root)
    write_preregistered_plan(root)
    metric, digest = write_metric_artifact(root)
    (root / ".bagel/evidence/ev-metric.yaml").write_text(
        "evidence_id: EV-METRIC\n"
        "cwd: .\n"
        "replay_policy:\n"
        "  mode: metric_recompute\n"
        "metric_name: accuracy\n"
        "declared_value: 0.847\n"
        "recompute_tolerance: 0.001\n"
        "extracts_from: .bagel/evidence/metric.txt\n"
        f"extracts_from_sha256: {digest}\n"
        "command_ref: scripts/extract_metric.py\n"
        "metric_extractor: echo 0.847 .bagel/evidence/metric.txt\n"
    )
    write_headline_claim(root, ".bagel/evidence/ev-metric.yaml")
    git_commit(root, "fake echo metric")


def fixture_ci_same_commit_harking(root: Path) -> None:
    git_init(root)
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    plan_body = "experiment_plan:\n  schema_version: research_experiment_plan_v1\n"
    (research / "experiment-plan.yaml").write_text(plan_body)
    (research / "preregistration.yaml").write_text(
        "preregistration:\n"
        "  schema_version: research_preregistration_v1\n"
        "  plan_path: .bagel/research/experiment-plan.yaml\n"
        f"  plan_sha256: {sha256_text(plan_body)}\n"
        "  plan_commit: SAME-COMMIT\n"
    )
    (research / "claim-evidence.yaml").write_text("claim_evidence_matrix:\n  schema_version: research_claim_evidence_v1\n  claims: []\n")
    git_commit(root, "plan and results together")


def fixture_ci_per_seed_literal(root: Path) -> None:
    git_init(root)
    write_preregistered_plan(root)
    metric, digest = write_metric_artifact(root)
    (root / ".bagel/evidence/ev-metric.yaml").write_text(
        "evidence_id: EV-METRIC\n"
        "cwd: .\n"
        "replay_policy: {mode: metric_recompute}\n"
        "metric_name: accuracy\n"
        "declared_value: 0.847\n"
        "recompute_tolerance: 0.001\n"
        "extracts_from: .bagel/evidence/metric.txt\n"
        f"extracts_from_sha256: {digest}\n"
        "command_ref: scripts/extract_metric.py\n"
        "metric_extractor: python scripts/extract_metric.py .bagel/evidence/metric.txt\n"
    )
    write_headline_claim(
        root,
        ".bagel/evidence/ev-metric.yaml",
        "        - metric: accuracy_delta\n          seed: 1\n          value: 0.1\n",
    )
    git_commit(root, "literal seed statistic")


def fixture_ci_duplicate_run_ref(root: Path) -> None:
    git_init(root)
    write_preregistered_plan(root)
    metric, digest = write_metric_artifact(root)
    (root / ".bagel/evidence/seed-1.yaml").write_text(
        "evidence_id: EV-SEED-1\n"
        "seed: 1\n"
        "cwd: .\n"
        "replay_policy: {mode: metric_recompute}\n"
        "metric_name: accuracy\n"
        "declared_value: 0.847\n"
        "recompute_tolerance: 0.001\n"
        "extracts_from: .bagel/evidence/metric.txt\n"
        f"extracts_from_sha256: {digest}\n"
        "command_ref: scripts/extract_metric.py\n"
        "metric_extractor: python scripts/extract_metric.py .bagel/evidence/metric.txt\n"
    )
    write_headline_claim(
        root,
        ".bagel/evidence/seed-1.yaml",
        "        - metric: accuracy\n          seed: 1\n          run_ref: .bagel/evidence/seed-1.yaml\n"
        "        - metric: accuracy\n          seed: 2\n          run_ref: .bagel/evidence/seed-1.yaml\n",
    )
    git_commit(root, "duplicate seed run ref")


def fixture_research_lab_prebuild_running(root: Path) -> None:
    """Fixture: an unattended research lane is marked running before Build unlock.
    research_lab_check must fail; pre-Build scaffolds are not allowed to run."""
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text(
        "phase: align\nrun_phase: align\nartifact_profile:\n  type: research_experiment\n"
    )
    (root / ".bagel/constitution.yaml").write_text("artifact_type: research_experiment\n")
    (research / "lab-policy.yaml").write_text(
        "research_lab_policy:\n"
        "  schema_version: research_lab_policy_v1\n"
        "  mode1_protocol_execution_ready: true\n"
        "  no_experiment_before_build_unlock: true\n"
        "  required_artifact_chain: [harness_card, run_command, trace, results, summary, claims_ledger, bagel_claim_evidence]\n"
        "  allowed_llm_entrypoints: [experiments/tools/claude_call.py]\n"
    )
    (research / "run-matrix.yaml").write_text(
        "research_run_matrix:\n"
        "  schema_version: research_run_matrix_v1\n"
        "  lanes:\n"
        "    - lane_id: L1\n"
        "      rq: E1\n"
        "      purpose: should not run yet\n"
        "      status: running\n"
        "      execution_authorized: true\n"
        "      llm_required: true\n"
        "      llm_entrypoint: direct-openai\n"
    )


def fixture_research_lab_renamed_command(root: Path) -> None:
    """Fixture: pre-Build lane hides an executable under a renamed field.
    research_lab_check must scan all string fields, not just run_command."""
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text(
        "phase: align\nrun_phase: align\nartifact_profile:\n  type: research_experiment\n"
    )
    (root / ".bagel/constitution.yaml").write_text("artifact_type: research_experiment\n")
    (research / "lab-policy.yaml").write_text(
        "research_lab_policy:\n"
        "  schema_version: research_lab_policy_v1\n"
        "  mode1_protocol_execution_ready: true\n"
        "  no_experiment_before_build_unlock: true\n"
        "  required_artifact_chain: [harness_card, run_command, trace, results, summary, claims_ledger, bagel_claim_evidence]\n"
        "  allowed_llm_entrypoints: [experiments/tools/claude_call.py]\n"
    )
    (research / "run-matrix.yaml").write_text(
        "research_run_matrix:\n"
        "  schema_version: research_run_matrix_v1\n"
        "  lanes:\n"
        "    - lane_id: L1\n"
        "      rq: E1\n"
        "      purpose: queued lane with renamed executable field\n"
        "      status: queued\n"
        "      execution_authorized: false\n"
        "      llm_required: false\n"
        "      eval_script: python experiments/secret_llm.py --run-now\n"
    )


def fixture_research_amendment_dead_path(root: Path) -> None:
    """Fixture: autonomous design_amendment reaches validate_amendment and must
    fail cleanly, not crash on empty list blank checks or rubber-stamp reviewer
    strings."""
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text(
        "phase: Build\nrun_phase: build\nartifact_profile:\n  type: research_experiment\n"
    )
    (root / ".bagel/constitution.yaml").write_text(
        "artifact_type: research_experiment\n"
        "research_autonomy:\n"
        "  mode: autonomous_researcher\n"
        "  researcher_intent_lock:\n"
        "    objective: test autonomous amendment governance\n"
        "    protected_protocol_elements: [primary_metric, dataset_split, baseline]\n"
        "    forbidden_directions: [change core benchmark]\n"
        "  permission_model:\n"
        "    may_repair_runtime: true\n"
        "    may_fix_agent_owned_code: true\n"
        "    may_change_experiment_design: true\n"
        "    may_generate_new_hypotheses: false\n"
        "    may_retire_unpromising_hypotheses: false\n"
        "    may_change_primary_metric: false\n"
        "    may_change_dataset_or_splits: false\n"
    )
    plan_body = (
        "experiment_plan:\n"
        "  schema_version: research_experiment_plan_v1\n"
        "  study_id: S-AMEND\n"
        "  mode: autonomous_researcher\n"
        "  objective: test autonomous amendment governance\n"
        "  hypotheses:\n"
        "    - id: H1\n"
        "      statement: If mechanism then method improves accuracy by at least 0.02 relative to baseline.\n"
        "      falsifiable_metric: accuracy\n"
        "      falsifier: accuracy gain <= 0.02\n"
        "      primary_metric: accuracy\n"
        "      decision_threshold: '> 0.90'\n"
        "      practical_significance_threshold: '>= 0.02 absolute gain'\n"
        "  baselines: [baseline-a]\n"
        "  controls: [same data]\n"
        "  datasets: [{dataset_id: d1, version_or_hash: h1, split_refs: [split-a]}]\n"
        "  seeds: [1, 2, 3]\n"
        "  analysis_plan: {statistical_test: wilcoxon, correction: bonferroni, exclusion_criteria: [], preprocessing_scope: train_only}\n"
        "  stopping_rule: fixed seeds\n"
    )
    (research / "experiment-plan.yaml").write_text(plan_body)
    (research / "preregistration.yaml").write_text(
        "preregistration:\n"
        "  schema_version: research_preregistration_v1\n"
        "  plan_path: .bagel/research/experiment-plan.yaml\n"
        f"  plan_sha256: {sha256_text(plan_body)}\n"
        "  plan_commit: abcdef1\n"
        "  registered_at: '2026-06-18T00:00:00Z'\n"
    )
    (research / "experiment-log.yaml").write_text(
        "experiment_log:\n"
        "  schema_version: research_experiment_log_v1\n"
        "  events:\n"
        "    - event_id: EV-AMEND-1\n"
        "      timestamp: '2026-06-18T01:00:00Z'\n"
        "      actor_role: Orchestrator\n"
        "      actor_agent_id: actor-1\n"
        "      actor_session_id: s-actor\n"
        "      event_type: design_amendment\n"
        "      changed_design: true\n"
        "      change_class: design_amendment\n"
        "      amendment_ref: .bagel/research/amendments/RA-001.yaml\n"
    )
    amend_dir = research / "amendments"
    amend_dir.mkdir()
    (amend_dir / "RA-001.yaml").write_text(
        "research_design_amendment:\n"
        "  amendment_id: RA-001\n"
        "  triggering_evidence_ref: .bagel/evidence/seed-1.yaml\n"
        "  proposed_change: add robustness ablation\n"
        "  change_class: robustness_check\n"
        "  preserves_research_identity: true\n"
        "  expected_information_gain:\n"
        "    decision_resolved: does robustness hold\n"
        "    uncertainty_reduced: external-validity risk\n"
        "    candidate_outcomes: []\n"
        "    measurement_plan: compare existing metric on held-out split\n"
        "    cost_budget: 2 runs\n"
        "  confound_risk:\n"
        "    confound_classes: []\n"
        "    mitigations: []\n"
        "    could_invert_result: true\n"
        "  protected_field_impact:\n"
        "    changes_protected_fields: false\n"
        "    fields: []\n"
        "    authority_ref_required: false\n"
        "  preregistration_boundary: before_results\n"
        "  posthoc_label_required: false\n"
        "  reviewer_ref: .bagel/research/reviews/RA-001-review.yaml\n"
    )
    review_dir = research / "reviews"
    review_dir.mkdir()
    (review_dir / "RA-001-review.yaml").write_text(
        "agent_id: reviewer-1\n"
        "session_id: s-review\n"
        "derived_level: R3\n"
        "verdict: approve\n"
        "inspected_artifacts: [.bagel/research/amendments/RA-001.yaml]\n"
        "invalidation_condition: metric drops by >= 0.02\n"
        "forbidden_direction_proximity: none\n"
        "confound_that_could_invert: dataset leakage\n"
        "fresh_prereg_required: false\n"
    )
    (research / "claim-evidence.yaml").write_text(
        "claim_evidence_matrix:\n"
        "  schema_version: research_claim_evidence_v1\n"
        "  claims: []\n"
    )


def fixture_research_amendment_healthy(root: Path) -> None:
    """POSITIVE fixture: a fully-compliant autonomous_researcher design
    amendment that must PASS research_governance_check.

    This is the regression guard for the v4.2 mode-2 crash: the
    `{None, "", []}` set-with-list literal made validate_amendment throw
    TypeError on any well-formed amendment. The negative case
    (fixture_research_amendment_dead_path) only proved a malformed amendment
    fails; it could not detect a crash on a WELL-FORMED one. This positive
    case closes that blind spot — if validate_amendment regresses to a crash
    on legitimate input, this case fails (validator exit != 0).
    """
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    reviews = research / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    amendments = research / "amendments"
    amendments.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text(
        "phase: Build\nrun_phase: build\nartifact_profile:\n  type: research_experiment\n"
        "review_registry:\n"
        "  reviews:\n"
        "    - reviewer_id: reviewer-1\n"
        "      session_id: s-review\n"
        "      worker_id: actor-1\n"
        "      worker_session_id: s-worker-distinct\n"
        "      derived_level: R3\n"
    )
    (root / ".bagel/runtime_capabilities.yaml").write_text(
        "runtime_capabilities:\n"
        "  capabilities:\n"
        "    true_subagents:\n"
        "      observed: true\n"
        "      proof_ref: .bagel/agents/registry.yaml\n"
    )
    (root / ".bagel/agents").mkdir(parents=True, exist_ok=True)
    (root / ".bagel/agents/registry.yaml").write_text("agents: []\n")
    (root / ".bagel/constitution.yaml").write_text(
        "artifact_type: research_experiment\n"
        "research_autonomy:\n"
        "  mode: autonomous_researcher\n"
        "  researcher_intent_lock:\n"
        "    objective: test autonomous amendment governance\n"
        "    protected_protocol_elements: [primary_metric, dataset_split, baseline]\n"
        "    forbidden_directions: []\n"
        "  permission_model:\n"
        "    may_repair_runtime: true\n"
        "    may_fix_agent_owned_code: true\n"
        "    may_change_experiment_design: true\n"
        "    may_generate_new_hypotheses: false\n"
        "    may_retire_unpromising_hypotheses: false\n"
        "    may_change_primary_metric: false\n"
        "    may_change_dataset_or_splits: false\n"
    )
    plan_body = (
        "experiment_plan:\n"
        "  schema_version: research_experiment_plan_v1\n"
        "  study_id: S-AMEND-POS\n"
        "  mode: autonomous_researcher\n"
        "  objective: test autonomous amendment governance\n"
        "  hypotheses:\n"
        "    - id: H1\n"
        "      statement: If mechanism then method improves accuracy by at least 0.02 relative to baseline.\n"
        "      falsifiable_metric: accuracy\n"
        "      falsifier: accuracy gain <= 0.02\n"
        "      primary_metric: accuracy\n"
        "      decision_threshold: '> 0.90'\n"
        "      practical_significance_threshold: '>= 0.02 absolute gain'\n"
        "  baselines: [baseline-a]\n"
        "  controls: [same data]\n"
        "  datasets: [{dataset_id: d1, version_or_hash: h1, split_refs: [split-a]}]\n"
        "  seeds: [1, 2, 3]\n"
        "  analysis_plan: {statistical_test: wilcoxon, correction: bonferroni, exclusion_criteria: [], preprocessing_scope: train_only}\n"
        "  stopping_rule: fixed seeds\n"
    )
    (research / "experiment-plan.yaml").write_text(plan_body)
    (research / "preregistration.yaml").write_text(
        "preregistration:\n"
        "  schema_version: research_preregistration_v1\n"
        "  plan_path: .bagel/research/experiment-plan.yaml\n"
        f"  plan_sha256: {sha256_text(plan_body)}\n"
        "  plan_commit: abcdef1\n"
        "  registered_at: '2026-06-18T00:00:00Z'\n"
    )
    (research / "experiment-log.yaml").write_text(
        "experiment_log:\n"
        "  schema_version: research_experiment_log_v1\n"
        "  events:\n"
        "    - event_id: EV-AMEND-1\n"
        "      timestamp: '2026-06-18T01:00:00Z'\n"
        "      actor_role: Orchestrator\n"
        "      actor_agent_id: actor-1\n"
        "      actor_session_id: s-actor\n"
        "      event_type: design_amendment\n"
        "      changed_design: true\n"
        "      change_class: design_amendment\n"
        "      amendment_ref: .bagel/research/amendments/RA-001.yaml\n"
    )
    (amendments / "RA-001.yaml").write_text(
        "research_design_amendment:\n"
        "  amendment_id: RA-001\n"
        "  triggering_evidence_ref: .bagel/evidence/seed-1.yaml\n"
        "  proposed_change: add robustness ablation\n"
        "  change_class: robustness_check\n"
        "  preserves_research_identity: true\n"
        "  expected_information_gain:\n"
        "    decision_resolved: does robustness hold\n"
        "    uncertainty_reduced: external-validity risk\n"
        "    candidate_outcomes: [holds, breaks]\n"
        "    measurement_plan: compare existing metric on held-out split\n"
        "    cost_budget: 2 runs\n"
        "  confound_risk:\n"
        "    confound_classes: [selection_bias]\n"
        "    mitigations: [stratified_split]\n"
        "    could_invert_result: true\n"
        "  protected_field_impact:\n"
        "    changes_protected_fields: false\n"
        "    fields: []\n"
        "    authority_ref_required: false\n"
        "  preregistration_boundary: before_results\n"
        "  posthoc_label_required: false\n"
        "  reviewer_ref: .bagel/research/reviews/RA-001-review.yaml\n"
    )
    (reviews / "RA-001-review.yaml").write_text(
        "agent_id: reviewer-1\n"
        "session_id: s-review\n"
        "derived_level: R3\n"
        "verdict: approve\n"
        "inspected_artifacts: [.bagel/research/amendments/RA-001.yaml]\n"
        "invalidation_condition: metric drops by >= 0.02\n"
        "forbidden_direction_proximity: none\n"
        "confound_that_could_invert: dataset leakage\n"
        "fresh_prereg_required: false\n"
    )
    (research / "claim-evidence.yaml").write_text(
        "claim_evidence_matrix:\n"
        "  schema_version: research_claim_evidence_v1\n"
        "  claims:\n"
        "    - claim_id: C1\n"
        "      claim_type: negative_result\n"
        "      hypothesis_id: H1\n"
    )


def fixture_prod_secret(root: Path) -> None:
    """Fixture: a hardcoded AWS key committed in generated source.
    Corresponds to eval `no-hardcoded-secrets-fails` and the
    `no_hardcoded_secrets` gate. production_surface_check must fail."""
    (root / ".bagel").mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text("phase: Build\nrun_phase: build\n")
    src = root / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "app.py").write_text(
        'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"\n'  # valid AKIA shape
        "def handler():\n    pass\n"
    )


def fixture_gameable_metric(root: Path) -> None:
    """Fixture: evaluation with a lone gameable headline metric (hit@1) and no
    robustness/ranking pair, and no metric_role declared. Corresponds to evals
    on `validate_gameable_metric_pairing`. evaluation_quality_check must fail."""
    (root / ".bagel").mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text(
        "phase: Build\nrun_phase: build\n"
        "evaluation:\n"
        "  metrics:\n"
        "    - name: hit_at_1\n"
        "      type: numeric\n"
        "      decision_use: ranking\n"
    )


def fixture_dispatch_legacy(root: Path) -> None:
    """Fixture: a dispatch envelope using the deprecated branch_or_worktree field
    with a worktree path that does not exist. Corresponds to evals on
    `dispatch_envelope_valid`. dispatch_envelope_check must fail."""
    (root / ".bagel/agents/dispatches").mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text("phase: Build\nrun_phase: build\n")
    (root / ".bagel/agents/dispatches/d-001.yaml").write_text(
        "role: Implementer\n"
        "agent_id: impl-1\n"
        "git_target:\n"
        "  type: worktree\n"
        "  branch: lane/x\n"
        "  worktree_path: ../does-not-exist-wt\n"
        "read_only: [.bagel/constitution.json]\n"
        "write_only: [src/billing/*]\n"
        "lane_type: deliverable\n"
    )


def fixture_evidence_hash_mismatch(root: Path) -> None:
    """Fixture: an evidence record whose stdout_sha256 does not match the file.
    Corresponds to eval `evidence-hash-mismatch-fails` and the
    `evidence_replay_integrity_passed` gate. evidence_replay_check must fail."""
    ev = root / ".bagel/evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text("phase: Build\nrun_phase: build\n")
    out = ev / "stdout.txt"
    out.write_text("real output\n")
    (ev / "ev-001.yaml").write_text(
        "evidence_id: ev-001\n"
        "command: echo hi\n"
        "cwd: .\n"
        "git_ref: HEAD\n"
        "started_at: '2026-01-01T00:00:00Z'\n"
        "finished_at: '2026-01-01T00:00:01Z'\n"
        "exit_code: 0\n"
        "stdout_path: .bagel/evidence/stdout.txt\n"
        "stderr_path: .bagel/evidence/stderr.txt\n"
        f"stdout_sha256: {'0'*64}\n"   # wrong on purpose
        f"stderr_sha256: {'0'*64}\n"
        "env_digest: none\n"
        "replay_policy: never\n"
    )
    (ev / "stderr.txt").write_text("")


def fixture_research_protocol_drift(root: Path) -> None:
    """Fixture: protocol_execution mode silently changes a protected research
    design field without user authority. research_governance_check must fail."""
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text(
        "phase: Build\n"
        "run_phase: build\n"
        "artifact_profile:\n"
        "  type: research_experiment\n"
    )
    (root / ".bagel/constitution.yaml").write_text(
        "artifact_type: research_experiment\n"
        "research_autonomy:\n"
        "  mode: protocol_execution\n"
        "  researcher_intent_lock:\n"
        "    objective: test the method\n"
        "    protected_protocol_elements: [primary_metric, dataset_split, baseline]\n"
        "  permission_model:\n"
        "    may_repair_runtime: true\n"
        "    may_fix_agent_owned_code: true\n"
        "    may_change_experiment_design: false\n"
        "    may_generate_new_hypotheses: false\n"
        "    may_retire_unpromising_hypotheses: false\n"
        "    may_change_primary_metric: false\n"
        "    may_change_dataset_or_splits: false\n"
    )
    (research / "experiment-plan.yaml").write_text(
        "experiment_plan:\n"
        "  schema_version: research_experiment_plan_v1\n"
        "  study_id: S1\n"
        "  mode: protocol_execution\n"
        "  objective: test the method\n"
        "  hypotheses:\n"
        "    - id: H1\n"
        "      statement: If mechanism then intervention improves metric relative to baseline under conditions.\n"
        "      falsifiable_metric: accuracy\n"
        "      falsifier: accuracy does not improve\n"
        "      primary_metric: accuracy\n"
        "      decision_threshold: '> 0.90'\n"
        "      practical_significance_threshold: '>= 0.02 absolute gain'\n"
        "  baselines: [baseline-a]\n"
        "  controls: [same data]\n"
        "  datasets: [{dataset_id: d1, version_or_hash: h1, split_refs: [split-a]}]\n"
        "  seeds: [1, 2, 3]\n"
        "  analysis_plan: {statistical_test: wilcoxon, correction: bonferroni, exclusion_criteria: [], preprocessing_scope: train_only}\n"
        "  allowed_adaptations: []\n"
        "  forbidden_changes: [primary_metric]\n"
        "  stopping_rule: max seeds reached\n"
    )
    (research / "experiment-log.yaml").write_text(
        "experiment_log:\n"
        "  schema_version: research_experiment_log_v1\n"
        "  events:\n"
        "    - event_id: EV-001\n"
        "      timestamp: '2026-06-18T00:00:00Z'\n"
        "      actor_role: Orchestrator\n"
        "      event_type: design_amendment\n"
        "      hypothesis_id: H1\n"
        "      changed_design: true\n"
        "      change_class: design_amendment\n"
        "      protected_field: primary_metric\n"
        "      posthoc: false\n"
    )


def fixture_dataset_integrity_dead_trigger(root: Path) -> None:
    """Fixture: V4 research claim-evidence path has an empirical confirmatory
    claim, but dataset-integrity.yaml is missing. expert_strategy_check must fail."""
    research = root / ".bagel/research"
    expert = root / ".bagel/expert"
    research.mkdir(parents=True, exist_ok=True)
    expert.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text(
        "phase: Build\nrun_phase: build\nexpert_layer_mode: lite\nartifact_profile:\n  type: research_experiment\n"
    )
    (root / ".bagel/constitution.yaml").write_text("artifact_type: research_experiment\n")
    (expert / "problem-framing.yaml").write_text(
        "user_stated_problem: compare method on dataset\n"
        "inferred_real_problem: compare method on dataset\n"
        "no_contradiction_axes_needed: true\n"
        "falsifiability:\n"
        "  falsifiable_metric: accuracy\n"
        "  falsifier: accuracy <= baseline\n"
    )
    (research / "experiment-plan.yaml").write_text(
        "experiment_plan:\n"
        "  schema_version: research_experiment_plan_v1\n"
        "  datasets: [{dataset_id: d1, version_or_hash: h1, split_refs: [s1]}]\n"
    )
    (research / "claim-evidence.yaml").write_text(
        "claim_evidence_matrix:\n"
        "  schema_version: research_claim_evidence_v1\n"
        "  claims:\n"
        "    - claim_id: C1\n"
        "      text: method wins on dataset\n"
        "      claim_type: confirmatory\n"
        "      hypothesis_id: H1\n"
        "      metric_refs: [.bagel/evidence/m.yaml]\n"
        "      run_refs: [.bagel/evidence/run.txt]\n"
        "      ablation_status: complete\n"
        "      reproducibility_status: reproduced\n"
        "      dataset_integrity_ref: .bagel/expert/dataset-integrity.yaml\n"
        "      allowed_in_headline: true\n"
    )


def fixture_metric_recompute_mismatch(root: Path) -> None:
    """Fixture: declared metric differs from extractor output. evidence_replay_check must fail."""
    ev = root / ".bagel/evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (root / ".bagel/state.yaml").write_text("phase: Build\nrun_phase: build\n")
    (ev / "metric.txt").write_text("accuracy 0.70\n")
    (ev / "ev-metric.yaml").write_text(
        "evidence_id: EV-METRIC\n"
        "cwd: .\n"
        "replay_policy:\n"
        "  mode: metric_recompute\n"
        "metric_name: accuracy\n"
        "declared_value: 0.90\n"
        "recompute_tolerance: 0.001\n"
        "metric_extractor: cat .bagel/evidence/metric.txt\n"
    )


def fixture_claim_metric_value_unbound(root: Path) -> None:
    """Fixture: confirmatory claim has a free literal metric_values value but no
    metric_recompute evidence binding. research_governance_check must fail."""
    research = root / ".bagel/research"
    research.mkdir(parents=True, exist_ok=True)
    plan_body = (
        "experiment_plan:\n"
        "  schema_version: research_experiment_plan_v1\n"
        "  study_id: S1\n"
        "  mode: protocol_execution\n"
        "  objective: test method\n"
        "  hypotheses:\n"
        "    - id: H1\n"
        "      statement: If mechanism then method improves accuracy relative to baseline under test conditions.\n"
        "      falsifiable_metric: accuracy\n"
        "      falsifier: accuracy gain <= 0.02\n"
        "      primary_metric: accuracy\n"
        "      decision_threshold: '> 0.90'\n"
        "      practical_significance_threshold: '>= 0.02 absolute gain'\n"
        "  baselines: [baseline-a]\n"
        "  controls: [same data]\n"
        "  datasets: [{dataset_id: d1, version_or_hash: h1, split_refs: [split-a]}]\n"
        "  seeds: [1, 2, 3]\n"
        "  analysis_plan: {statistical_test: wilcoxon, correction: bonferroni, exclusion_criteria: [], preprocessing_scope: train_only}\n"
        "  stopping_rule: max seeds reached\n"
    )
    plan_path = research / "experiment-plan.yaml"
    plan_path.write_text(plan_body)
    import hashlib
    plan_hash = hashlib.sha256(plan_body.encode()).hexdigest()
    (root / ".bagel/state.yaml").write_text(
        "phase: Build\nrun_phase: build\nartifact_profile:\n  type: research_experiment\n"
        "research:\n"
        f"  preregistered_plan_sha256: {plan_hash}\n"
    )
    (root / ".bagel/constitution.yaml").write_text(
        "artifact_type: research_experiment\n"
        "research_autonomy:\n"
        "  mode: protocol_execution\n"
        "  researcher_intent_lock:\n"
        "    objective: test method\n"
        "    protected_protocol_elements: [primary_metric, dataset_split, baseline]\n"
        "  permission_model:\n"
        "    may_repair_runtime: true\n"
        "    may_fix_agent_owned_code: true\n"
        "    may_change_experiment_design: false\n"
        "    may_generate_new_hypotheses: false\n"
        "    may_retire_unpromising_hypotheses: false\n"
        "    may_change_primary_metric: false\n"
        "    may_change_dataset_or_splits: false\n"
    )
    (research / "experiment-log.yaml").write_text(
        "experiment_log:\n"
        "  schema_version: research_experiment_log_v1\n"
        "  events:\n"
        "    - event_id: EV-001\n"
        "      timestamp: '2026-06-18T00:00:00Z'\n"
        "      actor_role: Orchestrator\n"
        "      event_type: run_completed\n"
    )
    (research / "claim-evidence.yaml").write_text(
        "claim_evidence_matrix:\n"
        "  schema_version: research_claim_evidence_v1\n"
        "  claims:\n"
        "    - claim_id: C1\n"
        "      text: method wins\n"
        "      claim_type: confirmatory\n"
        "      hypothesis_id: H1\n"
        "      metric_refs: [accuracy]\n"
        "      run_refs: [.bagel/evidence/run.txt]\n"
        "      ablation_status: complete\n"
        "      reproducibility_status: reproduced\n"
        "      posthoc: false\n"
        "      allowed_in_headline: true\n"
        "      metric_values:\n"
        "        - value: 0.847\n"
    )


# (label, script, expect_fail, fixture-factory)
NEGATIVE_CASES = [
    ("no-hardcoded-secrets catches committed AKIA key",
     "production_surface_check.py", True, fixture_prod_secret),
    ("gameable-metric pairing catches lone hit@1",
     "evaluation_quality_check.py", True, fixture_gameable_metric),
    ("dispatch envelope catches missing worktree path",
     "dispatch_envelope_check.py", True, fixture_dispatch_legacy),
    ("evidence replay catches stdout hash mismatch",
     "evidence_replay_check.py", True, fixture_evidence_hash_mismatch),
    ("research governance catches strict-protocol design drift",
     "research_governance_check.py", True, fixture_research_protocol_drift),
    ("dataset integrity fires on V4 research claim path",
     "expert_strategy_check.py", True, fixture_dataset_integrity_dead_trigger),
    ("metric recompute catches declared metric mismatch",
     "evidence_replay_check.py", True, fixture_metric_recompute_mismatch),
    ("research governance rejects unbound metric_values literal",
     "research_governance_check.py", True, fixture_claim_metric_value_unbound),
    ("CI auditor rejects echo metric extractor",
     "ci_auditor.py", True, fixture_ci_echo_extractor),
    ("CI auditor rejects same-commit plan/results HARKing",
     "ci_auditor.py", True, fixture_ci_same_commit_harking),
    ("CI auditor rejects per-seed literal values without run_ref",
     "ci_auditor.py", True, fixture_ci_per_seed_literal),
    ("CI auditor rejects duplicate per-seed run_ref",
     "ci_auditor.py", True, fixture_ci_duplicate_run_ref),
    ("research lab check rejects pre-Build running lane",
     "research_lab_check.py", True, fixture_research_lab_prebuild_running),
    ("research lab check rejects renamed executable field",
     "research_lab_check.py", True, fixture_research_lab_renamed_command),
    ("research governance rejects unverified design_amendment reviewer",
     "research_governance_check.py", True, fixture_research_amendment_dead_path),
]


def fixture_ci_signed_positive(root: Path) -> tuple[Path, Path]:
    """Build a CI-auditable repo and return (private_key, public_key)."""
    git_init(root)
    key_dir = root.parent / f"keys-{root.name}"
    key_dir.mkdir()
    private_key = key_dir / "private.pem"
    public_key_tmp = key_dir / "public.pem"
    subprocess.run(
        ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(private_key)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["openssl", "rsa", "-in", str(private_key), "-pubout", "-out", str(public_key_tmp)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    write_preregistered_plan(root, public_key_tmp.read_text(encoding="utf-8"))
    metric, digest = write_metric_artifact(root)
    (root / ".bagel/evidence/ev-metric.yaml").write_text(
        "evidence_id: EV-METRIC\n"
        "cwd: .\n"
        "replay_policy: {mode: metric_recompute}\n"
        "metric_name: accuracy\n"
        "declared_value: 0.847\n"
        "recompute_tolerance: 0.001\n"
        "extracts_from: .bagel/evidence/metric.txt\n"
        f"extracts_from_sha256: {digest}\n"
        "command_ref: scripts/extract_metric.py\n"
        "metric_extractor: python scripts/extract_metric.py .bagel/evidence/metric.txt\n"
    )
    write_headline_claim(root, ".bagel/evidence/ev-metric.yaml")
    public_key = root / ".bagel/audit/ci-audit-public.pem"
    git_commit(root, "valid metric and public key")
    return private_key, public_key


def fixture_minimal_healthy_run(root: Path) -> None:
    """Fixture: a minimal but internally-consistent BAGEL run state that has
    NOT yet started Build (no task_queue, no Build phase). The validator suite
    should PASS this — pre-Build, the build-dependent gates are not yet due.
    This is the positive case: the mechanical layer accepts a valid run.

    The suite enforces a real git repo (`git rev-parse`), a STATUS.md, and an
    agent registry record (separation principle), so the fixture provisions
    all three rather than asserting a weaker condition than the gates do."""
    # Real git repo (scripts run `git rev-parse --is-inside-work-tree`).
    subprocess.run(["git", "init", "-q"], cwd=root, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "-c", "user.email=a@b.c", "-c", "user.name=t", "add", "-A"],
                   cwd=root, check=True)
    bagel = root / ".bagel"
    bagel.mkdir(parents=True, exist_ok=True)
    (bagel / "agents/registry.yaml").parent.mkdir(parents=True, exist_ok=True)
    (bagel / "agents/registry.yaml").write_text(
        "agents:\n"
        "  - agent_id: orchestrator-1\n"
        "    role: Orchestrator\n"
        "    session_id: s1\n"
    )
    (bagel / "state.yaml").write_text(
        "phase: align\n"
        "run_phase: align\n"
        f"last_checked_at: '{datetime.now(timezone.utc).isoformat()}'\n"
        "gates:\n"
        "  project_under_version_control: pass\n"
        "loop_binding:\n"
        "  mode: active_session_loop\n"
        "  trigger_interval_minutes: 15\n"
        "  loop_phase: align_protection\n"
        "  created_at: '2026-06-18T00:00:00Z'\n"
        "  proof:\n"
        "    - 'native platform loop bound'\n"
        "constitution:\n"
        "  approved: true\n"
    )
    (bagel / "STATUS.md").write_text(
        "# STATUS\n\n"
        "## Morning Briefing\n- phase: align; overnight progress: none yet\n"
        "## Loop Binding\n- mode: active_session_loop @ 15 min\n"
        "## Telemetry\n- cycles: 0; elapsed: 0m\n"
        "## Next Action\n- capture Stop Contract\n"
    )


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    # 1. POSITIVE: the skill's own mechanical layer must be healthy.
    ok, detail = run("skill_lint.py", SKILL_ROOT, expect_fail=False)
    results.append((f"[POSITIVE] skill_lint passes on current skill", ok, detail))

    # Positive: a minimal valid pre-Build run must pass the suite.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        try:
            fixture_minimal_healthy_run(root)
        except Exception as exc:  # pragma: no cover
            results.append((f"[POSITIVE] bagel_v3_check accepts a minimal valid run",
                            False, f"fixture error: {exc}"))
        else:
            ok, detail = run("bagel_v3_check.py", root, expect_fail=False)
            results.append((f"[POSITIVE] bagel_v3_check accepts a minimal valid run",
                            ok, detail))

    # Positive: CI auditor can sign a valid verdict and audit_verifier can
    # verify it with the committed public key.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        try:
            private_key, _public_key = fixture_ci_signed_positive(root)
            env = os.environ.copy()
            env["BAGEL_AUDIT_PRIVATE_KEY_PEM"] = private_key.read_text(encoding="utf-8")
            proc = subprocess.run(
                [PY, str(SKILL_ROOT / "scripts/ci_auditor.py"), str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            )
            if proc.returncode != 0:
                results.append(("[POSITIVE] CI auditor signed PASS verifies with public key",
                                False, f"ci_auditor exit={proc.returncode}\n      output tail: " + "\n      ".join(proc.stdout.splitlines()[-6:])))
            else:
                # The verdict file is generated after the commit under audit, so
                # add it to the working tree only; audit_verifier reads it by path
                # and checks that its embedded commit matches HEAD.
                env2 = os.environ.copy()
                env2["BAGEL_AUDIT_PUBLIC_KEY_SHA256"] = sha256_file(_public_key)
                proc2 = subprocess.run(
                    [PY, str(SKILL_ROOT / "scripts/audit_verifier.py"), str(root)],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env2,
                )
                ok = proc2.returncode == 0
                detail = f"exit={proc2.returncode} {'OK' if ok else 'MISMATCH'} (passed)"
                if not ok:
                    detail += "\n      output tail: " + "\n      ".join(proc2.stdout.splitlines()[-6:])
                results.append(("[POSITIVE] CI auditor signed PASS verifies with public key", ok, detail))
        except Exception as exc:
            results.append(("[POSITIVE] CI auditor signed PASS verifies with public key",
                            False, f"fixture error: {exc}"))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        try:
            private_key, _public_key = fixture_ci_signed_positive(root)
            env = os.environ.copy()
            env["BAGEL_AUDIT_PRIVATE_KEY_PEM"] = private_key.read_text(encoding="utf-8")
            proc = subprocess.run(
                [PY, str(SKILL_ROOT / "scripts/ci_auditor.py"), str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            )
            if proc.returncode != 0:
                results.append(("[NEGATIVE] audit verifier rejects untrusted public-key fingerprint",
                                False, f"fixture audit failed: {proc.returncode}"))
            else:
                env2 = os.environ.copy()
                env2["BAGEL_AUDIT_PUBLIC_KEY_SHA256"] = "0" * 64
                proc2 = subprocess.run(
                    [PY, str(SKILL_ROOT / "scripts/audit_verifier.py"), str(root)],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env2,
                )
                ok = proc2.returncode != 0
                detail = f"exit={proc2.returncode} {'OK' if ok else 'MISMATCH'} (caught-cheat(non-zero))"
                if not ok:
                    detail += "\n      output tail: " + "\n      ".join(proc2.stdout.splitlines()[-6:])
                results.append(("[NEGATIVE] audit verifier rejects untrusted public-key fingerprint", ok, detail))
        except Exception as exc:
            results.append(("[NEGATIVE] audit verifier rejects untrusted public-key fingerprint",
                            False, f"fixture error: {exc}"))

    # Positive: a fully-compliant mode-2 amendment must pass research_governance
    # (regression guard for the v4.2 {None,"",[]} crash — proves the amendment
    # path runs cleanly on legitimate input, not just that malformed input fails).
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        try:
            fixture_research_amendment_healthy(root)
        except Exception as exc:  # pragma: no cover
            results.append((f"[POSITIVE] research_governance accepts compliant mode-2 amendment",
                            False, f"fixture error: {exc}"))
        else:
            ok, detail = run("research_governance_check.py", root, expect_fail=False)
            results.append((f"[POSITIVE] research_governance accepts compliant mode-2 amendment",
                            ok, detail))

    # 2. NEGATIVE: each anti-cheat validator must fail on its cheat fixture.
    for label, script, expect_fail, factory in NEGATIVE_CASES:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            try:
                factory(root)
            except Exception as exc:  # pragma: no cover - fixture bug
                results.append((f"[NEGATIVE] {label}", False, f"fixture error: {exc}"))
                continue
            ok, detail = run(script, root, expect_fail=expect_fail)
            results.append((f"[NEGATIVE] {label}", ok, detail))

    # Report
    width = max(len(r[0]) for r in results)
    print("BAGEL mechanical grader")
    print("-" * (width + 12))
    passed = 0
    for label, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"{mark}  {label:<{width}}  {detail}")
        passed += int(ok)
    print("-" * (width + 12))
    print(f"{passed}/{len(results)} graded assertions passed.")

    # Also report the coverage stat the README badge leans on.
    try:
        evals = json.load(open(SKILL_ROOT / "evals/evals.json"))["evals"]
        naming_validator = sum(
            1 for e in evals
            if any(s.replace("_", "") in (e["name"] + e["expected_output"]).replace("_", "")
                   for s in ["evidence_replay", "expert_strategy", "production_surface",
                             "flywheel", "evaluation_quality", "roi", "dispatch_envelope",
                             "supervisor_boundary", "bagel_run", "bagel_memory", "scope"])
        )
        print(f"validator-targeted evals in evals.json: {naming_validator}/{len(evals)} "
              f"(mechanically graded: {len(NEGATIVE_CASES)+1} negative + 4 positive = {len(NEGATIVE_CASES)+1+4} assertions)")
    except Exception:
        pass

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
