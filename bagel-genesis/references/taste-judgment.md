# Taste Judgment Protocol

Use for high-impact direction choices where numeric EV is not enough: innovation survivor selection, bar-raise direction, strategy switches after lateral cycles, final delivery acceptance, and constitution-level changes.

Do not use this protocol for ordinary slice implementation, tests, file naming, mechanical progress deltas, or STATUS.md data updates.

## Judgment Council

Dispatch at least three independent `agents/judgment-councilor.md` subagents. Each receives one dimension and cannot see other councilors' outputs.

Canonical dimensions:

```yaml
judgment_dimensions:
  - id: user_impact
    question: "Will users actually feel this as a meaningful improvement?"
    reject_if: "Users would not notice or experience gets worse."
  - id: elegance
    question: "Does this solve more with less complexity?"
    reject_if: "Complexity rises sharply while value barely rises."
  - id: coherence
    question: "Does this strengthen the product's core identity?"
    reject_if: "It conflicts with or dilutes the constitution north star."
  - id: durability
    question: "Will this still matter in six months?"
    reject_if: "It is a short-term patch with no durable value."
  - id: surprise
    question: "Would a user or reviewer remember this as unusually good?"
    boost_if: "Surprising and coherent, not surprising by going off-identity."
```

## Judgment Record

Write every council to `.bagel/decisions/judgment-<id>.yaml`:

```yaml
decision_id: "J-001"
decision_type: innovation_selection | bar_raise | strategy_switch | final_delivery | constitution_change
subject: "short decision title"
proposal_ref: ".bagel/innovation/ledger.yaml#PV-001"
required_dimensions: 3
councilors:
  - dimension: user_impact
    agent_id: "agent-judge-user-impact"
    session_id: "session-..."
    verdict: strong_yes
    reasoning: ""
    evidence_cited: []
  - dimension: elegance
    agent_id: "agent-judge-elegance"
    session_id: "session-..."
    verdict: yes
    reasoning: ""
    evidence_cited: []
  - dimension: coherence
    agent_id: "agent-judge-coherence"
    session_id: "session-..."
    verdict: neutral
    reasoning: ""
    evidence_cited: []
merge_result:
  status: passed | vetoed | disputed
  rule: "strong_no veto; strong_yes>=2 and no no/strong_no passes; otherwise disputed"
  strong_yes_count: 1
  no_count: 0
  strong_no_count: 0
  judgment_passed: false
  disagreement_summary: ""
```

## Merge Rules

This is not majority vote.

- Any `strong_no` means `status: vetoed`.
- `strong_yes_count >= 2` and `no_count == 0` and `strong_no_count == 0` means `status: passed`.
- All other outcomes are `status: disputed`.

Disputed is not failure. Record the disagreement and either gather more evidence, run a cheap probe, or revisit in a later iteration. Do not let the Orchestrator override the council with free-form preference.

## Taste-Adjusted EV

Normal EV ranking penalizes high-variance ideas before they have metrics. When `judgment_passed: true`, reduce the execution threshold by one point:

```text
normal:         ev_score >  cost_score + risk_score
taste_adjusted: ev_score >= cost_score + risk_score - 1
```

This does not waive cost/risk. It only compensates for ideas whose value is undercounted before a probe exists.

## Final Delivery

Final delivery requires a `decision_type: final_delivery` judgment record with `merge_result.status: passed`. Any `strong_no` means the run is not complete; dispatch repair, polish, or scope-specific recovery.
