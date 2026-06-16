# Reference Loading Telemetry

Use to keep progressive disclosure honest. A reference read must have a trigger and, when stable, should use a digest cache instead of repeated full reads.

Record:

```yaml
reference_reads:
  - reference: references/excellence-loop.md
    trigger: "bar_raise decision due"
    read_mode: full | digest | cached_fact
    source_hash: ""
    token_estimate: 8400
    cached_digest_used: false
```

Store stable digests under `.bagel/agent_context/reference-digests/`.

Cache stable facts under `.bagel/agent_context/cached-facts.yaml` or `state.yaml.cached_facts`:

```yaml
cached_facts:
  runtime_capabilities:
    source_ref: ".bagel/runtime_capabilities.yaml"
    source_hash: ""
    cached_at: "ISO-8601"
    run_id: ""
    valid_until: "ISO-8601 or source_hash_change"
    facts: {}
```

Build/Iterate requires reference-read telemetry or an explicit `lite_minimal` waiver. Repeated full reads of a stable reference more than twice in one run fail unless the source hash changed.

Run:

```bash
python scripts/reference_load_check.py <project-root>
```
