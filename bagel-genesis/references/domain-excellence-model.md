# Domain Excellence Model

Use during alignment/exploration before Build and whenever artifact type or target audience changes.

This answers: in this task, what does excellent actually mean?

```yaml
domain_excellence_model:
  model_id: ""
  created_at: "ISO-8601"
  updated_at: "ISO-8601"
  constitution_hash: ""
  artifact_profile_hash: ""
  domain: ""
  artifact_type: software | research | writing | design | data | mixed
  source_basis:
    - internal_exemplar
    - user_exemplar
    - repo_evidence
    - domain_standard
    - literature_or_external_reference
    - inferred_with_uncertainty
  what_excellent_means:
    - trait: ""
      observable_signal: ""
      why_it_matters: ""
      weak_version: ""
      strong_version: ""
      evidence_or_probe: ""
  top_1_percent_work:
    - exemplar: ""
      relevant_trait: ""
      how_this_project_can_approximate_it: ""
  mediocre_work: []
  common_failure_modes:
    - failure: ""
      how_to_detect: ""
      prevention: ""
  hidden_quality_dimensions:
    - dimension: ""
      why_amateurs_miss_it: ""
      probe: ""
  evaluation_traps: []
  reference_exemplars: []
  anti_exemplars: []
  expert_review_questions: []
  unacceptable_shortcuts: []
```

Generic adjective alone is invalid. Words like `robust`, `scalable`, `user-friendly`, `polished`, `high quality`, or `excellent` must be paired with observable signal, weak version, strong version, and evidence/probe.

Refresh this model when constitution hash, artifact profile hash, target audience, artifact type, or primary success definition changes.

For existing projects, exemplars may be internal: best existing module, best screen, best chapter, strongest experiment, strongest report section.

If the domain bar is unknown and the task is high-stakes, dispatch research/cartography before locking evaluation or strategy.
