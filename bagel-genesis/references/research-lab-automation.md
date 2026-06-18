# Research Lab Automation Protocol

Use when a BAGEL run will execute many experiments, benchmark tools, run
ablations, collect data, aggregate results, or prepare paper-ready empirical
claims without the researcher supervising each job.

## Researcher-Useful Autonomy

The researcher should spend attention on framing, taste, interpretation, and
final scientific judgment. BAGEL owns the engineering lab work:

- turn the approved protocol into a run matrix;
- schedule path-disjoint lanes and continue other lanes when one blocks;
- repair runtime/environment failures without changing protocol semantics;
- collect traces, logs, manifests, results, and summaries;
- draft claim-ledger entries and BAGEL claim-evidence records;
- run deterministic verification before any number reaches the paper.

Wake the researcher only for protected protocol changes, budget expansion,
dataset/model/metric changes, core research-identity changes, posthoc-to-
confirmatory promotion, or external publication/submission.

## Mode 1: Protocol Execution Lab

Mode 1 is the production workhorse. The agent is an automation lab technician
with strong debugging ability, not a co-PI.

Required files:

```yaml
research_lab_policy:
  schema_version: research_lab_policy_v1
  mode1_protocol_execution_ready: true
  mode2_autonomous_researcher_ready: false
  no_experiment_before_build_unlock: true
  required_artifact_chain: [harness_card, run_command, trace, results, summary, claims_ledger, bagel_claim_evidence]
  allowed_llm_entrypoints: []
  required_verifier_checks: [method_drift, code_correctness, trace_integrity, derivation, summary_match, paper_claim, cross_version]
```

```yaml
research_run_matrix:
  schema_version: research_run_matrix_v1
  study_id: ""
  lanes:
    - lane_id: ""
      rq: ""
      purpose: ""
      status: queued          # queued|blocked|running|completed|failed|frozen
      execution_authorized: false
      llm_required: false
      llm_entrypoint: ""
      protected_fields: []
      planned_artifacts: {}
```

Pre-Build, every lane must be `queued`, `blocked`, or `frozen`, and
`execution_authorized` must be false. Build unlock changes only the lane
authorization, not the protected protocol.

V4.3 treats pre-Build execution as a semantic property, not a field-name
property. `research_lab_check.py` recursively scans every string value in each
lane and rejects executable command patterns before Build unlock, including
commands hidden under renamed fields such as `eval_script`, `setup`, `execute`,
or nested metadata. It also scans all lane strings for LLM call signals and
requires routing through the single canonical entrypoint:
`experiments/tools/claude_call.py`. Declaring `llm_entrypoint` while invoking a
different LLM wrapper is a hard failure.

For any active/result lane (`running`, `completed`, `failed`), require:

- `harness_card`;
- `run_command`;
- `trace_glob`;
- `results_glob`;
- `aggregate_or_verify_command`;
- `claims_ledger_ref`;
- metric recompute evidence for every headline number.

Once Build starts, paper-grade research runs must also include
`.bagel/research/environment-lock.yaml` with Python/platform/package-freeze
hash and deterministic-seed flags. Pre-Build scaffolds are exempt so an agent
can prepare a protocol without running experiments.

Never substitute fake outputs for failed LLM/API calls. Record the lane as
`failed_api_no_fallback`, isolate it if needed, and continue another lane.

## Mode 2: Autonomous Researcher Upgrade

Mode 2 is not "mode 1 plus more freedom." It requires a stronger artifact:
each proposed design change must include expected information gain, confound
risk, protected-field impact, whether relevant results were already seen, and
independent reviewer evidence.

Enable mode 2 only after mode 1 reliably produces:

- complete run matrices;
- clean trace/result/ledger chains;
- verifier-ready audit packets;
- negative/null result preservation;
- no unapproved design drift over at least one real study.

Mode 2 may propose ablations, robustness checks, baseline strengthening, and
reanalysis. It still cannot autonomously change the core research identity,
datasets/splits, primary metrics, model axes, paid budget, or claim status.

## Harness4Testing Adapter Pattern

For Harness4Testing, lock these as protected protocol elements:

- Q/RQ identity and section mapping;
- HumanEval, LiveCodeBench cutoff slice, SWE-bench Live cutoff slice;
- descriptive-metric policy unless the Researcher explicitly authorizes tests;
- `experiments/tools/claude_call.py` as the only sanctioned LLM entrypoint;
- `docs/claims-ledger.md` as the paper-number ledger;
- verifier separation from experiment-runner and paper-writer.

The required chain is:

```text
harness_card.yaml
  -> run.sh + src/*.py
  -> traces/*.jsonl
  -> results/*.csv
  -> result_summary.md
  -> docs/claims-ledger.md
  -> .bagel/research/claim-evidence.yaml
```

Every lane should end by producing a verifier packet: commands run, manifest,
trace count, aggregation command, result CSV, summary, proposed ledger rows,
claim-evidence rows, and top-3 likely-wrong notes.
