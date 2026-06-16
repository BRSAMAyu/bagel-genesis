# Artifact Type Profiles

Use before defining skeletons, gates, QA, simulations, and excellence criteria. BAGEL is not only for software.

## Required Artifact

Create `.bagel/artifact_profile.yaml`:

```yaml
artifact_profile:
  primary_type: software_product | existing_software | research | writing | document_deck | data_analysis | mixed
  secondary_types: []
  baseline_unit: value_slice | chapter | section | experiment | dataset | deliverable_module
  skeleton_gate: ghost_ship | outline | protocol | template | analysis_pipeline | mixed
  verification_modes:
    - automated_tests
  non_applicable_gates:
    - "forbidden_visuals"
  required_quality_dimensions:
    - correctness
    - coherence
```

## Profiles

| Type | Baseline Unit | Skeleton Gate | Verification |
|---|---|---|---|
| `software_product` | value slice | runnable shell/Ghost Ship | tests, typecheck, e2e/CLI/browser evidence |
| `existing_software` | bounded improvement | current-behavior preservation gate | regression checks, diff review, project-context freshness |
| `research` | claim/experiment/section | research protocol + bibliography map | citation checks, methodology critique, reproducibility notes |
| `writing` | chapter/scene/argument section | outline + voice/continuity bible | continuity, structure, voice, reader-experience critique |
| `document_deck` | section/slide group | template + narrative spine | render checks, layout QA, factual review |
| `data_analysis` | dataset/question/chart | data pipeline + assumptions map | data validation, reproducibility, statistical critique |
| `mixed` | typed module | explicit per-module profile | combine only relevant gates |

## Artifact-Specific Lens Packs

Project understanding and takeover review must use lenses that fit the artifact type. Do not hard-code software lenses for research, writing, or data work.

```yaml
lens_packs:
  software:
    required_min_lenses: 2
    lenses: [structure, behavior, convention, surface]
  existing_software:
    required_min_lenses: 2
    lenses: [structure, behavior, convention, surface]
  research:
    required_min_lenses: 2
    lenses: [methodology, evidence, argument, reproducibility]
  writing:
    required_min_lenses: 2
    lenses: [structure, voice, pacing, continuity]
  document_deck:
    required_min_lenses: 2
    lenses: [structure, visual_hierarchy, narrative, readability]
  data_analysis:
    required_min_lenses: 2
    lenses: [schema, provenance, transformation, validation]
```

`scripts/bagel_run_check.py` validates the recorded lenses against the active artifact profile.

## Applicability Rules

- Visual/design-token gates apply only to visual artifacts or when visual presentation affects quality.
- Loading/empty/error/retry states apply to interactive software, CLIs, data pipelines, and external integrations; they do not apply to prose unless reinterpreted as reader/onboarding/failure modes.
- Typed contracts apply to APIs, data, AI pipelines, external integrations, structured research claims, or analysis schemas.
- Ghost Ship applies to software/app artifacts. For non-software, use the profile's skeleton gate.
- Code style heuristics apply only to code. For research/writing, use domain quality checks instead.

## Profile-Specific Coverage

For `artifact_specific_slice_coverage_present`, require the relevant set:

- Software: happy path, edge/error states, regression tests, setup/run evidence.
- Existing software: preserved behavior, changed behavior, no duplicate implementation, rollback evidence.
- Research: claim-evidence map, source quality, counterarguments, reproducibility, limitations.
- Writing: outline fit, continuity, pacing, voice, unresolved plot/argument issues.
- Document/deck: rendered output, layout, hierarchy, factual consistency, export/readability.
- Data analysis: data provenance, cleaning assumptions, validation checks, chart/table correctness.
