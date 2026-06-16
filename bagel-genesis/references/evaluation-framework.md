# Evaluation Framework Protocol

Use this before Build starts, at the start of every iteration, when a new artifact type appears, when a metric is gamed or stale, and before final delivery. BAGEL must not rely on a generic checklist; it must generate the evaluation system that fits the actual task.

## Principle

Evaluation is a decision engine, not a report. Every metric, rubric, verifier, and review question must say what decision it controls: candidate ranking, iteration completion, bar raising, strategy switch, recovery priority, or final delivery.

If a criterion does not change a decision, remove it. If a decision lacks criteria, dispatch `Evaluation Architect` before deciding.

## Required Evaluation Spec

Persist the active evaluation frame in quick mode under `.bagel/state.yaml#evaluation` or full mode under `.bagel/evaluation/current.yaml`:

```yaml
evaluation:
  active_spec_ref: ".bagel/evaluation/iteration-01.yaml"
  generated_by: "Evaluation Architect"
  applies_to: "iteration|slice|research_hypothesis|ui_polish|final_delivery"
  artifact_type: "software|research|writing|data|mixed"
  quality_questions: []
  metrics: []
  qualitative_rubric: []
  completion_rule: "all metrics green + required review findings resolved + no regression floors broken"
  decision_hooks:
    ranks_candidates: true
    gates_iteration_completion: true
    gates_final_delivery: false
  refreshed_at: "ISO-8601"
```

Each metric must include:

- `signal`: what real quality it reflects,
- `command_or_procedure`: how evidence is produced,
- `target`,
- `direction`,
- `anti_gaming_note`,
- `decision_use`.

Each qualitative rubric item must include:

- concrete pass/fail standards,
- reviewer role,
- evidence expected,
- whether it blocks completion or only informs ranking.

## Dispatch Rules

Dispatch `Evaluation Architect` for:

- first target-set creation,
- every new iteration target set,
- research hypothesis evaluation,
- UI/UX or taste-heavy work where metrics alone are insufficient,
- final delivery evaluation,
- any time three lateral cycles suggest the current criteria are wrong,
- any time a reviewer says the metric can be gamed.

The Orchestrator may choose between already-generated evaluation specs, but must not invent a new evaluation体系 from its own live context for a high-impact decision.

## Relationship To Judgment Council

Evaluation Architect designs the criteria. Judgment Council applies high-level taste judgment to direction choices. They are different:

- Evaluation Architect: "What evidence would show this is better?"
- Judgment Council: "Is this direction worth doing and coherent with the product?"

For high-impact choices, use both: first evaluation spec, then Judgment Council verdict using that evidence.

## Refresh And Replacement

Replace a metric when:

- it is green but reviewers still find serious quality gaps,
- it rewards trivial or harmful behavior,
- it no longer matches the iteration goal,
- artifact type or product direction changed,
- it cannot be run and no practical evidence procedure exists.

Record replacements in the evolution ledger with the old metric, reason, and new decision-useful signal.
