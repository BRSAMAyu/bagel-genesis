# Alignment Freshness and Taste Drift

Use at iteration end, after user instruction changes, before final delivery, and whenever product direction, UX, writing voice, research framing, or taste-sensitive output changes.

Do not use a self-score. The Curator or Reviewer must cite evidence.

```yaml
alignment_freshness:
  last_reanchor_cycle: 7
  last_reanchor_at: "ISO-8601"
  constitution_hash: "sha256..."
  taste_kernel_hash: "sha256..."
  current_work_summary: ""
  consistency:
    vision: pass | drift_risk | fail
    non_goals: pass | drift_risk | fail
    taste: pass | drift_risk | fail
    autonomy_contract: pass | drift_risk | fail
  reviewer_ref: ".bagel/reviews/alignment-freshness-007.yaml"
```

If any field is `fail`, switch strategy or enter recovery. `drift_risk` is not a stop signal; it requires a concrete repair or clarifying probe.

Run:

```bash
python scripts/alignment_freshness_check.py <project-root>
```
