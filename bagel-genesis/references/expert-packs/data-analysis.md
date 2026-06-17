# Data Analysis Expert Pack

```yaml
expert_pack:
  artifact_type: data_analysis
  top_1_percent_traits: [schema_validity, provenance, leakage_control, outlier_handling, chart_correctness, interpretation_robustness]
  common_amateur_failures: [silent_type_errors, leakage, misleading_axis, unsupported_causality, survivorship_bias, denominator_errors]
  hidden_quality_dimensions: [join_semantics, missingness_pattern, sensitivity_to_filters, temporal_leakage, groupby_correctness]
  evaluation_traps: [pretty_chart, row_count_only, correlation_story, cherrypicked_subset]
  minimum_evidence: [schema_check, provenance_note, transformation_log, validation_queries, sensitivity_analysis]
  useful_metrics: [validation_failures, missingness_rate, reconciliation_delta, leakage_test_pass]
  qualitative_rubric: [interpretation_humility, chart_truthfulness, robustness]
  red_team_questions: [Can this be leakage?, Is the denominator right?, What changes if outliers move?, Does the result survive a different time window?]
  breakthrough_operators_to_prioritize: [bottleneck_inversion, adversarial_reframing, frontier_gap_search]
  final_delivery_standard: "Analysis is reproducible, validated, and interpretations are bounded by evidence."
```

## Data Analysis Methodology

### §1 — Provenance first (before any transformation)
Every column must trace to a source. Record `.bagel/expert/data-provenance.yaml` with: source system, extraction date, row count at extraction, known quality issues. An analysis without provenance is unfalsifiable — you cannot reproduce or audit it.

### §2 — Leakage detection (mandatory before modeling)
Check these leakage vectors before any train/test split or model fitting:
- **Temporal leakage**: future data in features (e.g. using `is_churned` computed after the prediction window)
- **Group leakage**: same entity in train and test (split by `entity_id`, not random row)
- **Label leakage**: features derived from the target (e.g. `days_until_churn` as a feature)
- **Selection bias**: filtering on a post-outcome variable
Record the leakage check in dataset-integrity.yaml `leakage_vectors_checked`.

### §3 — Schema validation (before analysis)
Assert expected dtypes, ranges, and cardinalities. A silent type coercion (string "null" → NaN, integer → float) corrupts downstream analysis. Run `validate_schema()` against the declared schema and record failures.

### §4 — Transformation log (reproducibility)
Every transformation (filter, join, aggregate, derive) must be recorded as a numbered step in `.bagel/evidence/transformation-log.yaml` with: input columns, operation, output columns, rows affected. An analysis that cannot be re-run from the log is not reproducible.

### §5 — Outlier and missingness audit
Before drawing conclusions, audit: outlier fraction per column, missingness pattern (MCAR/MAR/MNAR), and sensitivity of the headline result to outlier removal. A result that flips when 1% of outliers are removed is not robust.

### §6 — Chart truthfulness
Every chart must: start axes at a defensible origin (not truncated to exaggerate), label units, show uncertainty (CI/error bars) where applicable, and avoid dual-axis tricks that imply false correlation. A chart that misleads is worse than no chart.

### §7 — Interpretation humility
Distinguish: descriptive (what happened) vs inferential (likely cause) vs predictive (what will happen). A correlation is not a causal claim. Every conclusion must state its scope (what population, what time window, what conditions) and what would falsify it.

### §8 — Sensitivity analysis (mandatory for headline claims)
A headline data claim must survive: (a) removing 5% of outliers, (b) a different time window, (c) a different aggregation level. Record the sensitivity result in the claim-evidence matrix. A claim that survives only one configuration is fragile.
