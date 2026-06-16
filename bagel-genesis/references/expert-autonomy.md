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

The required record uses the single `expert_decision_v1` schema:

```yaml
expert_decision:
  schema_version: expert_decision_v1
  decision_id: ""
  decision_type: framing | iteration_target | major_route | breakthrough_probe | strategy_switch | bar_raise | final_delivery | identity_or_scope_change
  decision_owner: {role: Principal Expert, agent_id: "", session_id: ""}
  options_considered:
    - option_id: ""
      option: ""
      expected_value: ""
      risk: ""
      uncertainty: ""
      evidence_refs: []
      council_refs: []
  selected_option_id: ""
  selected_direction: ""
  expert_thesis: ""
  why_this_now: ""
  rejected_alternatives:
    - option_id: ""
      why_rejected: ""
      decisive_evidence_or_assumption: ""
  participants:
    - role: ""
      agent_id: ""
      session_id: ""
      output_ref: ""
  domain_model_ref: ".bagel/expert/domain-excellence.yaml"
  problem_framing_ref: ".bagel/expert/problem-framing.yaml"
  leverage_map_ref: ".bagel/expert/leverage-map.yaml"
  evaluation_critic_ref: ""
  roi_ref: ".bagel/expert/roi-controller.yaml"
  confidence: low | medium | high
  reversibility: reversible | costly | irreversible
  risk_level: low | medium | high | critical
  risk_basis:
    affected_surfaces: []  # auth | privacy | payment | production_data | architecture | dependencies | user_identity | legal | financial
    scope_delta_ref: ""
    hard_stop_check_ref: ""
    reversibility_reason: ""
  authority_ref: ""  # required when reversibility is costly/irreversible
  decisive_evidence: []
  biggest_uncertainty: ""
  kill_criteria:
    - criterion: ""
      check_method: ""
      action_if_triggered: ""
  next_probe_or_action: ""
  hard_stop_triggered: false
```

Invalid if:

- no named Principal Expert decision owner,
- no rejected alternative,
- no domain calibration,
- metric cannot distinguish weak from excellent,
- disputed/vetoed judgment overridden without new evidence,
- no kill criteria for the selected direction.

The Orchestrator may coordinate the gate. It must not substitute its own preference for the Principal Expert record.
