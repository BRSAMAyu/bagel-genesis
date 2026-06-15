# Innovation Protocol

Use when the user wants novelty, a blank-slate product needs a strong concept, a run has locally optimized into a plateau, or the artifact's core decision space may be too narrow. This protocol adds divergent exploration without letting novelty silently corrupt the user's constitution.

## Principle

Execution quality cannot rescue a bad product decision. BAGEL must sometimes spend budget on high-variance concept exploration before it spends the night perfecting the wrong thing.

Innovation is not a license to drift. It is a governed exploration lane:

```text
diverge -> score novelty/fit/risk/evidence -> probe cheaply -> adopt, park, or reject
```

## Alignment Choice: Innovation Ambition

Capture this during alignment when the artifact is product, creative, research, game, strategy, or user asks for originality:

```yaml
innovation_contract:
  ambition: execution_excellence | differentiated | breakthrough
  exploration_budget_share: 0 | 10 | 20
  allow_identity_challenge: false
  novelty_floor: none | at_least_one_probe | multiple_competing_concepts
  user_must_approve_identity_change: true
```

- `execution_excellence`: optimize a supplied concept. No required divergent probes.
- `differentiated`: reserve about 10% of early budget for novel mechanics, framing, or UX probes.
- `breakthrough`: reserve about 20% of early budget and require multiple competing concept probes before locking the final direction.

If omitted, default to `differentiated` for blank-slate apps/products and `execution_excellence` for existing-project preservation work.

## Product Visionary Dispatch

Dispatch `agents/product-visionary.md` when:

- `innovation_contract.ambition` is `differentiated` or `breakthrough`,
- the user requests innovation/novelty/wow,
- three consecutive lateral cycles suggest the current frame is exhausted,
- bar-raising produced only low-value local polish.

Use at least two distinct lenses for `breakthrough`; one lens is enough for `differentiated` unless the first pass is quiet.

## Innovation Ledger

Record concept candidates in `.bagel/innovation/ledger.yaml`:

```yaml
concepts:
  - id: "PV-001"
    title: ""
    source_agent: "agent-id"
    lenses: [paradigm_shift]
    novelty_type: paradigm_shift | cross_domain_transfer | inversion | new_mechanic | constraint_as_feature | surprise | distribution
    fit_with_constitution: high | medium | low
    expected_upside: high | medium | low
    risk: low | medium | high
    hard_stop_risk: false
    constitution_change_needed: false
    falsifiable_probe: ""
    decision: probe | adopt | park | reject
    decision_reason: ""
    evidence:
      - ".bagel/evidence/innovation/PV-001-probe.md"
```

Do not delete rejected concepts. A rejected high-novelty idea is useful memory if the reason is clear.

## Novelty-Aware Selection

Normal EV ranking penalizes uncertainty. For innovation lanes, use two-stage selection:

1. Select cheap probes by upside and learning value, not only immediate EV.
2. After probe evidence exists, route survivors back through normal EV/risk/cost ranking.

Reject a concept only when one of these is true:

- it conflicts with a hard-stop or constitution boundary,
- its probe is too costly for the exploration budget,
- the probe evidence is negative,
- it is novel but does not improve user value.

## Constitution Boundary

The Product Visionary may challenge the current product concept, but it cannot mutate the constitution. If a concept requires changing the core promise, target audience, safety posture, privacy model, business model, or research identity:

1. park it as `constitution_change_needed: true`,
2. send it to Constitutional Court for risk framing,
3. wake the user unless the autonomy contract explicitly delegates that class of identity change.

## Astonishing If

If `.bagel/constitution.yaml.excellence_horizon.astonishing_if` is empty, the Orchestrator must dispatch Product Visionary or Brainstormer to propose candidates. Store accepted candidates in the constitution and rejected candidates in `.bagel/innovation/ledger.yaml`.
