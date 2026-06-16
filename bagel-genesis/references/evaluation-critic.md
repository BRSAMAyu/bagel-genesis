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
  fails_bad_example: ""
  passes_strong_example: ""
  detects_expert_quality_not_generic_checklist: ""
```

If the metric cannot discriminate, it cannot gate iteration completion.
