# V2 Measured Autonomous Runtime

V2 turns BAGEL from a declarative protocol into a measured runtime.

The core V2 guarantees:

- runtime capabilities are `observed` with proof, not assumed from adapter claims;
- evidence is replayable or explicitly non-replayable with reviewer evidence;
- non-root context replacement is driven by telemetry;
- handoffs are validated before a fresh child continues;
- actions are idempotent or explicitly unsafe to retry;
- governance work cannot be the only progress for too long;
- scope expansion is detected before it becomes silent drift;
- alignment/taste freshness is checked with evidence;
- the main validator is `scripts/bagel_v2_check.py`.

Run:

```bash
python scripts/bagel_v2_check.py <project-root>
```

Individual checks remain callable for diagnosis.
