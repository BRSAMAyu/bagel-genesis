# Packaging Boundary

Human docs are not runtime prompt context.

Human-facing repository docs:

- `/README.md`
- `/README.zh-CN.md`
- `bagel-genesis/README.md`

Skill runtime payload:

- `bagel-genesis/SKILL.md`
- `bagel-genesis/agents/`
- `bagel-genesis/references/`
- `bagel-genesis/scripts/`
- `bagel-genesis/evals/`

Workers should not read README files as operational authority unless explicitly asked to update human documentation. Runtime authority lives in SKILL, references, scripts, and `.bagel/` state.
