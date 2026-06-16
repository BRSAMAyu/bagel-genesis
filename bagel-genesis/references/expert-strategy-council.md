# Expert Strategy Council

Use for high-impact strategy decisions. This is not the same as Taste Judgment.

Recommended independent perspectives:

| Perspective | Question |
|---|---|
| Domain Expert | Does this meet the domain excellence model? |
| Systems Architect | Is this route structurally high-leverage? |
| Evaluation Skeptic | Will our metrics be fooled? |
| Innovation Strategist | Is there a better non-local route? |
| User Proxy | Does this serve the user's real goal? |
| Risk Officer | Is this overreach or irreversible risk? |

The Principal Expert synthesizes the council into one `expert_decision` record. The Orchestrator records and enforces it.

## Required Dispatch

Council participants must be real subagent dispatches, not an Orchestrator-written table. Every participant in `expert_decision_v1.participants` must match a registry/dispatch record by `role`, `agent_id`, and `session_id`, and must cite an existing `output_ref`.

Required for normal strategy decisions:

- Domain Expert
- Evaluation Skeptic
- User Proxy

Also required when applicable:

- Systems Architect for architecture, major route, or costly integration choices
- Risk Officer for high/critical risk or irreversible/costly choices
- Innovation Strategist for breakthrough probes or breakthrough ambition

Each councilor writes:

```yaml
expert_council_verdict:
  perspective: Domain Expert | Systems Architect | Evaluation Skeptic | Innovation Strategist | User Proxy | Risk Officer
  agent_id: ""
  session_id: ""
  option_under_review: ""
  verdict: support | reject | needs_probe | outside_authority
  key_reason: ""
  evidence_refs: []
  missing_evidence: []
  kill_criteria_suggestion: []
```

## Council Result

```yaml
council_result:
  status: passed | vetoed | disputed | deadlocked | needs_probe
  quorum:
    aligned_count: 0
    total: 0
    threshold: 0
  next_required_action: principal_expert_decision | gather_more_evidence | cheap_probe | user_checkpoint
```

Vetoes cannot be overridden without new evidence or Constitutional Court. Deadlock requires a cheap probe, more evidence, or a user checkpoint. The Principal Expert may resolve `disputed` only with decisive evidence recorded in `new_decisive_evidence_ref`.
