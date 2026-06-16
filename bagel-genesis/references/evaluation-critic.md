# Evaluation Critic Protocol

Use immediately after Evaluation Architect creates or refreshes an evaluation spec.

The critic asks whether the evaluation system can actually distinguish expert-quality work from shallow proxy wins.

```yaml
evaluation_critic:
  critic_agent_id: ""
  review_ref: ".bagel/reviews/evaluation-critic-001.yaml"
  metric_correlates_with_real_quality: pass | fail
  metric_not_easy_to_game: pass | fail
  covers_user_value: pass | fail
  covers_domain_excellence: pass | fail
  negative_examples: []
  baseline_comparison: []
  surface_overfit_risk: low | medium | high
```

Each primary metric should include:

```yaml
metric_discrimination_check:
  bad_example:
    description: ""
    expected_metric_result: ""
    why_bad: ""
  strong_example:
    description: ""
    expected_metric_result: ""
    why_strong: ""
  distinguishes_bad_from_strong: true
  evidence_ref: ""
```

If the metric cannot discriminate, it cannot gate iteration completion.

If `surface_overfit_risk: high`, the metric cannot be an iteration completion gate unless a compensating qualitative rubric covers the quality that the metric misses.
