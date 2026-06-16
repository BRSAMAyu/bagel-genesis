# Expert Autonomy Layer

Use before Build starts, at each iteration start, after three lateral cycles, before breakthrough probes, and before final delivery.

V3 goal: BAGEL should not only run honestly; it should make high-level decisions like a top expert team.

## High-Impact Decision Gate

Trigger when deciding:

- problem framing,
- iteration target set,
- major architecture/product/research route,
- breakthrough probe,
- strategy switch,
- bar-raise direction,
- final delivery,
- identity or scope change.

Required inputs:

```yaml
expert_autonomy_gate:
  trigger: framing | iteration_target | major_route | breakthrough_probe | strategy_switch | final_delivery | identity_or_scope_change
  required_inputs:
    - active_evaluation_spec
    - expert_context_packet
    - domain_excellence_model
    - problem_framing
    - leverage_map
    - competing_options_or_reason_only_one_exists
    - judgment_council_record_when_taste_sensitive
    - probe_or_metric_evidence
    - roi_controller
  decision_owner: Principal Expert
  required_record: ".bagel/expert/strategy-decisions/<id>.yaml"
```

Invalid if:

- no named Principal Expert decision owner,
- no rejected alternative,
- no domain calibration,
- metric cannot distinguish weak from excellent,
- disputed/vetoed judgment overridden without new evidence,
- no kill criteria for the selected direction.

The Orchestrator may coordinate the gate. It must not substitute its own preference for the Principal Expert record.
