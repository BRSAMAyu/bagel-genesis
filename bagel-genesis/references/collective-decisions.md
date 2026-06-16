# Collective Decisions Protocol

Use when a BAGEL decision is directional, high-impact, hard to reverse, or likely to benefit from genuinely different perspectives.

Do not use multi-agent ceremony for routine reversible implementation. The point is useful group intelligence, not appearing multi-agent.

## Decision Map

| Decision point | Participants | Why it deserves group intelligence | Merge rule |
|---|---|---|---|
| Innovation direction selection | Product Visionary generates; Judgment Council evaluates; Orchestrator records | Directional decision; wrong choice can waste the run | Taste Judgment veto/pass/disputed rules |
| Bar-raise direction | >=2 Brainstormers generate; Judgment Council evaluates | The next target set determines where optimization goes | Taste Judgment veto/pass/disputed rules |
| Strategy switch after 3 lateral cycles | Red-Team diagnoses; Brainstormer proposes alternatives; Judgment Council evaluates switch | Wrong strategy can burn remaining budget | Any strong_no blocks; passed/disputed recorded |
| Hard-gate recovery path | Independent Reviewer diagnoses; Orchestrator selects recovery ladder step | Recovery path affects future integrity | Reviewer diagnosis constrains options; record chosen path |
| Final delivery acceptance | Spec Reviewer, Code Quality Reviewer, Red-Team Oracle, Judgment Council | Delivery quality and taste are multi-dimensional | Any P0/P1 or strong_no blocks delivery |
| Constitution change | Constitutional Court plus Judgment Council | Identity-level and hard to reverse | Court veto + Judgment Council veto both apply |

## Explicit Non-Use Cases

Do not dispatch a council for:

- ordinary slice implementation choices,
- test writing details,
- file naming or local structure covered by conventions,
- mechanical `forward/lateral/backward` classification,
- STATUS.md mechanical telemetry updates.

## Independence Rules

Every participant in a collective decision must have:

- separate subagent context,
- a distinct role or dimension,
- no access to other participants' outputs until all return,
- structured return artifacts with evidence links.

The Orchestrator merges only after all artifacts exist. Consensus and disagreement are both recorded; disagreement is useful state, not an error to hide.

## Records

Write collective decision records under `.bagel/decisions/`:

```yaml
decision_id: "CD-001"
decision_point: bar_raise | innovation_selection | strategy_switch | final_delivery | constitution_change
participants:
  - role: Brainstormer
    agent_id: ""
    lens_or_dimension: novelty
  - role: Judgment Councilor
    agent_id: ""
    lens_or_dimension: user_impact
merge_rule: "taste_judgment_veto"
result: passed | vetoed | disputed | selected_path
evidence:
  - ".bagel/decisions/judgment-J-001.yaml"
```

If a high-impact decision was made without a collective record, the run must explain why it was below the collective-decision threshold.

## Adaptive Bar-Raise Policy

Do not run maximum ceremony for every mechanical target adjustment. Use this policy:

```yaml
bar_raise_policy:
  mechanical_tightening:
    examples: ["coverage 80->85", "benchmark +5% target"]
    brainstormers_required: 0
    judgment_required: false
  new_quality_dimension:
    brainstormers_required: 2
    judgment_required: optional
  direction_change:
    brainstormers_required: 2
    judgment_required: true
  innovation_probe:
    brainstormers_required: 2
    product_visionary_required: true
    judgment_required: true
```

The purpose is not fewer agents by default; it is to spend group intelligence where direction quality matters.
