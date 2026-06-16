# Leverage Map Protocol

Use at iteration start and after poor/stalled results.

The leverage map answers: what action is most likely to unlock a large quality jump?

```yaml
leverage_map:
  bottlenecks:
    - id: B-001
      type: evaluation | architecture | UX | theory | data | tooling | narrative | performance | strategy
      current_evidence: []
      why_it_limits_quality: ""
      candidate_interventions: []
      expected_value: high | medium | low
      uncertainty: high | medium | low
      cheapest_probe: ""
  top_leverage_action:
    bottleneck_id: B-001
    action: ""
    why_this_now: ""
```

The next iteration target set must cite the leverage map. If it does not, it is just a task list, not expert strategy.
