# Research Governance Protocol

Use for research, experiments, benchmarks, theory-to-experiment work, data analysis with empirical claims, and autonomous scientific iteration. This file defines the two BAGEL research modes and the durable records required to keep long-running research honest, reproducible, and reviewable.

## Mode Declaration

Every research-like run must declare exactly one mode in `.bagel/constitution.yaml`:

```yaml
research_autonomy:
  mode: protocol_execution | autonomous_researcher
  researcher_intent_lock:
    objective: ""
    protected_hypotheses: []
    protected_protocol_elements: [primary_metric, decision_threshold, dataset_split, baseline, exclusion_criteria, analysis_plan]
    forbidden_directions: []
  permission_model:
    may_repair_runtime: true
    may_fix_agent_owned_code: true
    may_change_experiment_design: false
    may_generate_new_hypotheses: false
    may_retire_unpromising_hypotheses: false
    may_change_primary_metric: false
    may_change_dataset_or_splits: false
  escalation_policy:
    design_change_requires: human_authority_ref
    core_research_identity_change: hard_stop
  preregistered_plan_sha256: ""  # write once at Build unlock; validator rejects mutation
```

`protocol_execution` is the strict tool mode. The agent executes the researcher's protocol, repairs local runtime/code/environment failures, and records everything. It must not introduce new hypotheses, change the primary metric, alter data splits, alter thresholds, remove baselines, change exclusion criteria, reinterpret the research question, or present post-hoc analyses as confirmatory without explicit human authority.

`autonomous_researcher` is the scientific collaborator mode. The agent may propose and run design improvements, new ablations, alternative hypotheses, extra robustness checks, and negative-result follow-ups inside the locked research direction. It still may not change the core research identity, use restricted data, touch human-subject/clinical/compliance surfaces, spend paid resources, or make external non-rollbackable effects without a hard-stop decision.

## Required Research Artifacts

Before Build unlock, create `.bagel/research/experiment-plan.yaml`, commit it before any result artifact, compute its sha256, and write `.bagel/research/preregistration.yaml`. CI treats `state.yaml` and `constitution.yaml` hashes as agent-writable hints only; the authoritative pin is the preregistration record:

```yaml
preregistration:
  schema_version: research_preregistration_v1
  plan_path: ".bagel/research/experiment-plan.yaml"
  plan_sha256: ""
  plan_commit: ""       # first commit introducing experiment-plan.yaml
  audit_public_key_sha256: ""
  command_pins:
    - path: "experiments/run_one.py"
      sha256: ""
      purpose: "approved experiment entrypoint"
  registered_at: "ISO-8601"
  registered_by: "Researcher | Orchestrator"
  approval_ref: ""      # human decision id if Build unlock is user-approved
```

Then maintain the plan itself:

```yaml
experiment_plan:
  schema_version: research_experiment_plan_v1
  study_id: ""
  mode: protocol_execution | autonomous_researcher
  objective: ""
  hypotheses:
    - id: H1
      statement: "If <mechanism>, then <intervention> will produce <change> on <metric>, relative to <baseline>, under <conditions>."
      falsifiable_metric: ""
      falsifier: ""
      primary_metric: ""
      decision_threshold: ""
      practical_significance_threshold: ""
      confirmatory: true
  baselines: []
  controls: []
  datasets:
    - dataset_id: ""
      version_or_hash: ""
      split_refs: []
  seeds: []
  analysis_plan:
    statistical_test: ""
    correction: ""
    exclusion_criteria: []
    preprocessing_scope: train_only | train_val | all_data
  allowed_adaptations: []
  forbidden_changes: []
  stopping_rule: ""
```

During execution, maintain `.bagel/research/experiment-log.yaml` as the durable event log:

```yaml
experiment_log:
  schema_version: research_experiment_log_v1
  events:
    - event_id: EV-001
      timestamp: "ISO-8601"
      actor_role: Orchestrator | Runtime Doctor | Implementer | Evaluation Architect | Principal Expert
      event_type: plan_registered | run_started | run_completed | runtime_repair | code_fix | design_amendment | analysis_completed | claim_recorded | negative_result
      hypothesis_id: H1
      command_ref: ""
      evidence_ref: ""
      result_ref: ""
      changed_design: false
      change_class: none | runtime_repair | implementation_bugfix | design_amendment | posthoc_analysis | core_identity_change
      authority_ref: ""
      posthoc: false
      notes: ""
      amendment_ref: ""  # required for design_amendment/posthoc_analysis/core_identity_change
```

Every final or interim research claim must map to `.bagel/research/claim-evidence.yaml`:

```yaml
claim_evidence_matrix:
  schema_version: research_claim_evidence_v1
  claims:
    - claim_id: C1
      text: ""
      claim_type: confirmatory | exploratory | negative_result | limitation
      hypothesis_id: H1
      metric_refs: []
      run_refs: []
      ablation_status: complete | partial | missing | not_applicable
      reproducibility_status: reproduced | single_run | missing
      dataset_integrity_ref: ".bagel/expert/dataset-integrity.yaml"
      posthoc: false
      allowed_in_headline: true
      metric_values:
        - metric: ""
          value: 0.0
          evidence_ref: "EV-METRIC-001"  # must resolve to metric_recompute evidence
          seed: null
          run_ref: ""                    # required for per-seed statistic inputs
```

## Protocol Execution Mode

In `protocol_execution`, a change is allowed autonomously only if it preserves the registered design:

- runtime/environment repairs that do not alter protocol semantics;
- fixes to agent-written code bugs that restore the intended protocol;
- verifier creation, logging, checksum generation, and result extraction;
- retrying failed jobs with the same preregistered seeds/config;
- isolating a broken lane while continuing another preregistered lane.

The following require `authority_ref` from an interactive user decision before execution: changing the hypothesis, baseline, primary metric, decision threshold, dataset, split, seed policy, exclusion criteria, statistical test, analysis plan, or interpretation standard. A post-hoc exploratory analysis may be added, but it must be labeled `posthoc: true` and cannot support a confirmatory headline claim unless rerun under a fresh preregistered plan.

In V4.1, `authority_ref` is not a free string. It must resolve to `.bagel/ledger.yaml human_decisions[]` with `decision_type: research_design_change`, matching `protected_fields`, approved status, and a decision timestamp no later than the event timestamp.

## Autonomous Researcher Mode

In `autonomous_researcher`, the agent may improve the design, but only through explicit amendments:

```yaml
research_design_amendment:
  amendment_id: RA-001
  timestamp: "ISO-8601"
  triggering_evidence_ref: ""
  proposed_change: ""
  change_class: new_ablation | robustness_check | alternative_hypothesis | metric_addition | baseline_strengthening | analysis_refinement
  preserves_research_identity: true
  expected_information_gain:
    decision_resolved: ""
    uncertainty_reduced: ""
    candidate_outcomes: []
    measurement_plan: ""
    cost_budget: ""
  confound_risk:
    confound_classes: []
    mitigations: []
    could_invert_result: true
  protected_field_impact:
    changes_protected_fields: false
    fields: []
    authority_ref_required: false
  preregistration_boundary: before_results | after_results
  posthoc_label_required: true | false
  reviewer_ref: ""
  fresh_preregistration_ref: ""  # required for after_results/posthoc amendments before confirmatory use
  baseline_strength_delta:
    metric: ""
    before: ""
    after: ""
```

If the amendment occurs after relevant results were seen, mark it `posthoc_label_required: true`. Post-hoc results are valuable for discovery but cannot be promoted to confirmatory claims without a fresh preregistered rerun.

V4.3 validation requires each design amendment to cite R3/R4 reviewer evidence, preserve research identity, declare structured expected information gain, structured confound risk, protected-field impact, and avoid overlap with `forbidden_directions`. The reviewer report must include inspected artifacts, approve/pass verdict, and adversarial fields: invalidation condition, forbidden-direction proximity, confound that could invert the result, and whether a fresh preregistration is required. A `baseline_strengthening` amendment must include `baseline_strength_delta`.

R3/R4 reviewer evidence is not self-declared. It must be backed by `runtime_capabilities.capabilities.true_subagents.observed: true` with an existing `proof_ref`, and by `.bagel/agents/registry.yaml` or `state.review_registry` deriving R3/R4 independence for the reviewer/worker pair. Same-thread role switching remains R1/R2 and cannot approve autonomous research amendments.

Any after-results/posthoc amendment needs `fresh_preregistration_ref` before it can support a confirmatory rerun. The fresh preregistration must exist, include a different `plan_sha256` from the original plan, include `plan_commit`, and have `registered_at` no earlier than the amendment event. Confirmatory claims originating from an amendment must include `originating_amendment_ref`, `prereg_plan_ref`, and `rerun_event_refs`; posthoc amendments can only become confirmatory when `prereg_plan_ref` equals the amendment's fresh preregistration.

Autonomous researcher mode has a mechanical drift limit: more than five design-change events or more than two protected-field-touching amendments require human review before continuing. This is a guardrail against sequential p-hacking; it is not a substitute for the researcher's scientific judgment.

## Metric Recompute Evidence

Headline/confirmatory claims must cite metric recompute evidence. Each confirmatory claim's `metric_values[]` entry must include `evidence_ref`, pointing to an evidence record with `replay_policy.mode: metric_recompute` (or `not_replayable` plus a `metric_extractor`). A free literal such as `metric_values: [{value: 0.847}]` is rejected. The evidence record provides a `metric_extractor` command that reads saved logs/results and prints the metric value. The validator reruns the extractor and compares it with `declared_value` within `recompute_tolerance`; this does not require rerunning expensive training.

CI-level headline evidence is stricter: metric evidence must include `extracts_from` and `extracts_from_sha256`, and the extractor must reference that artifact. A trivial extractor that prints a literal (`echo 0.847`, `printf`, `python -c 'print(...)'`) is not evidence. Per-seed statistics must cite `run_ref` evidence for each seed; YAML-only seed values are refused.

## Environment Lock

Once research Build starts, capture `.bagel/research/environment-lock.yaml`:

```yaml
environment_lock:
  schema_version: research_environment_lock_v1
  python_version: ""
  platform: ""
  package_freeze_sha256: ""  # sha256 of the committed freeze/lock artifact
  created_at: "ISO-8601"
  determinism:
    pythonhashseed: ""
    seed_policy: ""
    torch_deterministic: true | false | not_applicable
```

This artifact is intentionally small. It records the environment needed to interpret paper-grade numbers without pretending the validator can reproduce every CUDA or system dependency itself.

## Non-Negotiable Research Hard Stops

Wake the user before any action involving human subjects, clinical/medical advice, regulated data, privacy-sensitive data, live external systems, paid compute beyond the Stop Contract, credentials, production infrastructure, external publication/submission/posting/email, or a change to the core research identity. These are SKILL.md hard-stop boundaries applied to science.

## Final Scientific Delivery

The final report must include:

- registered objective, hypotheses, metrics, thresholds, baselines, controls, seeds, and data hashes;
- all runs, including failures and negative/null results;
- ablations, sensitivity analyses, statistical tests, corrections, and practical significance checks;
- claim-evidence matrix with confirmatory vs exploratory labels;
- reproducibility commands and environment;
- design amendments and whether they were pre-result or post-hoc;
- limitations, threats to validity, and what would falsify the conclusion next.
