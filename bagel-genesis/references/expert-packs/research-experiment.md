# Research Experiment Expert Pack

```yaml
expert_pack:
  artifact_type: research_experiment
  top_1_percent_traits: [clear_hypothesis, strong_baseline, ablation, confidence, reproducibility, honest_claims]
  common_amateur_failures: [no_baseline, cherry_picked_metric, hidden_data_leakage, vague_theory, single_seed_win, unfalsifiable_claim]
  hidden_quality_dimensions: [negative_results, sensitivity_analysis, claim_evidence_matrix]
  evaluation_traps: [single_seed_win, benchmark_overfit, posthoc_story]
  minimum_evidence: [hypothesis, baseline, metric, controls, reproducibility_plan]
  useful_metrics: [effect_size, confidence_interval, ablation_delta, reproduction_success]
  qualitative_rubric: [method_soundness, evidence_strength, theory_update]
  red_team_questions: [What alternative explains the effect?, Does it survive ablation?, Is the baseline fair?, Would it hold on a second seed?, Are FLOPs/latency measured, not assumed?]
  breakthrough_operators_to_prioritize: [first_principles_reduction, adversarial_reframing, frontier_gap_search]
  final_delivery_standard: "Claims match evidence, baselines are fair, and reproduction path is clear."
```

## Experimental methodology (mandatory procedure)

These are the executable procedures that turn a hypothesis into a falsifiable, reproducible result. An experiment without all of these is not deliverable — it is a preliminary observation.

### 1. Falsifiable hypothesis
State one sentence of the form: **"If <mechanism>, then <intervention> will produce <predicted measurable change> on <metric>, relative to <baseline>, under <conditions>."** If you cannot fill every slot, the hypothesis is not yet testable — reframe it (see `references/problem-framing.md`) before running anything. Record the falsifier: the exact result that would make you reject the hypothesis.

### 2. Controlled setup
- **Baseline**: a fair, strong baseline, not a strawman. For ML: same data, same compute budget, same training recipe; isolate only the variable under test. For systems: same hardware, same workload, same warm-up.
- **Controls**: list every variable held constant and every variable that differs. Data leakage check: train/val/test splits fixed and disjoint; no test data in tuning.
- **Random seeds**: run at least **3 seeds** for any stochastic result (default 5 for headline claims). Record every seed. Single-seed wins are red-flagged by `evaluation_traps`.

### 3. Metrics with discrimination
- **Primary metric**: pre-registered before running, one number that decides the hypothesis (e.g. val_bpb, FLOPs/token, p95 latency).
- **Cost metric**: report alongside — compute (FLOPs or GPU-hours), latency, memory. A quality win that costs 3× compute is a different claim than a free win.
- **Variance**: report mean ± std across seeds. For n<3, mark the result as preliminary and never use it in a headline claim. Report confidence intervals where applicable.

### 4. Ablation matrix
For every component of the proposed method, run one row that removes or replaces it. The matrix answers "which part actually causes the effect?" Minimum: ablate the core mechanism, the auxiliary mechanisms, and re-add them one at a time. A result that survives full ablation is robust; a result that collapses under ablation is a confound, not a finding.

### 5. FLOP / cost accounting (when the claim involves efficiency)
When the claim is "lower FLOPs at equal quality" (e.g. sparse activation / MoE routing), measure FLOPs, do not estimate them from parameter count. Report: total FLOPs per forward pass, active FLOPs (routed), FLOPs/token, and quality at matched compute. Compare at **iso-compute**, not just iso-parameters — MoE often trades parameters for routing FLOPs. Measure wall-clock latency and peak memory too; theoretical FLOP savings that do not show up as latency savings are not a delivered efficiency win.

### 6. Reproducibility package
Before claiming a result is reproducible, all of these exist:
- fixed seeds recorded for every run;
- data preparation script + dataset version/hash;
- exact commands to re-run baseline and method;
- environment (package versions / hardware);
- raw logs + the metric extraction step.
A reviewer running the commands on the recorded environment must reach the same conclusion. If any piece is missing, the claim is downgraded to "not independently reproducible" and flagged in `.bagel/evidence/`.

### 7. Honest claims
Every claim in the final report maps to a row in a claim-evidence matrix: claim → metric → run(s) → ablation status → reproducibility status. Claims that outrun their evidence are rejected before delivery. Negative results and null findings are recorded, not hidden — `common_amateur_failures: hidden_data_leakage` includes hidden negative results.
