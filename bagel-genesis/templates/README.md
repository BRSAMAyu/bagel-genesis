# BAGEL producer-side templates

These are fill-in-the-blank templates for the artifacts the validators police. They
exist to close the **execution gap**: an agent is far more likely to produce a
schema-correct artifact when it copies a template and fills the blanks than when it
must reconstruct the schema from a reference doc. Each template is annotated with
exactly what the corresponding gate checks, so "fill the template honestly" and "pass
the gate" are the same act.

| Template | Fill it when | Gate it satisfies |
|---|---|---|
| `optimization-target.yaml` | Starting an Optimizer run (`objective: optimization`), before any gain | `optimization_integrity_clean` |
| `optimization-log.yaml` | Throughout an Optimizer run — log **every** variant tried | `optimization_integrity_clean` |
| `discovery-frame.yaml` | Starting an Explorer run (`objective: discovery`), step 0 | (rubric for `discovery_sandbox_clean` selection) |
| `discovery-report.yaml` | Delivering an Explorer run's vetted ideas | `discovery_sandbox_clean` |
| `reproducibility-checklist.yaml` | Any research run with a confirmatory/headline claim | `reproducibility_checklist_complete` |
| `data-hygiene.yaml` | Any research run with a confirmatory/headline claim | `data_hygiene_leakage_free` |

Copy a template into the path the gate reads (shown at the top of each file), delete
the guidance comments if you like, and fill every field with the truth. Do not invent
fields or rename them — the gates match field names exactly. A template field you
cannot fill honestly is a signal the work is not done, not a field to delete.
