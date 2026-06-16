# Breakthrough Search Protocol

Use when innovation ambition is `breakthrough`, when three cycles are lateral, or when local polish no longer changes the quality frontier.

Operators:

```yaml
breakthrough_search:
  operators_used:
    - first_principles_reduction
    - bottleneck_inversion
    - analogy_transfer
    - adversarial_reframing
    - constraint_as_feature
    - remove_assumed_requirement
    - change_unit_of_optimization
    - exploit_tooling_affordance
    - expert_embarrassment_test
    - frontier_gap_search
```

Each candidate must answer:

```yaml
candidate:
  what_assumption_it_breaks: ""
  why_existing_solution_space_misses_it: ""
  why_it_could_be_10x_better: ""
  cheapest_falsifiable_probe: ""
  risk_if_wrong: ""
  evidence_needed_to_adopt: ""
  adoption_threshold: ""
  rejection_threshold: ""
  breakthrough_quality:
    changes_unit_of_optimization: true | false
    attacks_primary_bottleneck: true | false
    asymmetric_upside: true | false
    cheap_probe_under_budget: true | false
    falsifies_core_assumption: true | false
    creates_option_value: true | false
```

For `breakthrough`, require at least three operators, three competing product/research theses, and at least two true `breakthrough_quality` properties per candidate before Principal Expert selection.
