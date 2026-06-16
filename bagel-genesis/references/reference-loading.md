# Reference Loading Telemetry

Use to keep progressive disclosure honest. A reference read must have a trigger and, when stable, should use a digest cache instead of repeated full reads.

Record:

```yaml
reference_reads:
  - reference: references/excellence-loop.md
    trigger: "bar_raise decision due"
    read_mode: full | digest
    token_estimate: 8400
    cached_digest_used: false
```

Store stable digests under `.bagel/agent_context/reference-digests/`.

Run:

```bash
python scripts/reference_load_check.py <project-root>
```
