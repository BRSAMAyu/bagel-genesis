# Dataset Integrity

Use when a research or experiment run makes empirical claims based on a dataset. The goal is to make held-out leakage and test-set tuning detectable by the validator, not just promised by the agent.

## Required record

`.bagel/expert/dataset-integrity.yaml`:

```yaml
dataset_integrity:
  dataset_id: ""
  dataset_version_or_hash: ""
  split_strategy: random | stratified | temporal
  train_split_hash: ""
  val_split_hash: ""
  test_split_hash: ""
  split_disjointness_check_ref: ""   # script/log proving train/val/test are disjoint
  tuning_used_test_set: false        # true = test set was used for tuning -> headline claim invalid
  preprocessing_fit_on: train_only | train_val | all_data
  all_data_justification: ""         # required only if preprocessing_fit_on=all_data
  leakage_checks: [duplicate_rows, target_leakage, temporal_leakage, identity_overlap]
  holdout_policy: ""                 # how the held-out set is kept truly held-out
  rerun_commands: []                 # exact commands to reproduce baseline + method
```

## Rules (enforced by `expert_strategy_check.py`)

1. Empirical dataset-based claims require this record. Missing it fails.
2. Train/val/test split hashes must exist for dataset-based claims.
3. `split_disjointness_check_ref` is required — there must be proof the splits are disjoint.
4. `tuning_used_test_set: true` invalidates the headline claim — the test set was touched during tuning.
5. `preprocessing_fit_on: all_data` without `all_data_justification` fails (potential leakage: preprocessing saw test data).

## Why schema-level, not semantic

A script cannot judge whether a research conclusion is correct, but it CAN verify that the integrity artifacts exist and are self-consistent (split hashes present, disjointness checked, test-set tuning flagged). This catches the most common held-out trick: the agent attests a held-out set exists but never proves it is disjoint, or quietly fit preprocessing on all data. The agent-attested fields are still semantic judgments, but the structural honesty (hashes present, tuning flag set) is mechanically checked.
