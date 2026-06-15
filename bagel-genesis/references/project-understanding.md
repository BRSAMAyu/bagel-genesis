# Existing Project Understanding Protocol

Use this before BAGEL modifies an existing or partially implemented project. The goal is to understand the current project reality deeply enough that future agents can work without re-exploring the whole codebase each time.

## Core Rule

Do not overwrite the user's existing project mental model with assumptions. Build an evidence-backed model of the current project, compare it with the user's desired direction, then align.

## Two Audiences

Maintain two separate documentation surfaces:

- **Agent-facing context** in `.bagel/agent_context/`: compact, factual, operational, optimized for future workers.
- **Human-facing briefing** in `.bagel/user_briefing/`: explanatory, decision-oriented, optimized for user understanding and trust.

Never merge these into one bloated document. Agent-facing context prevents drift; human-facing briefing supports decisions.

## Intake Outputs

First create `.bagel/project_inventory/takeover-scope.yaml`:

```yaml
takeover:
  mode: limited_takeover | full_takeover
  target_root: "."
  allowed_bagel_location: ".bagel"
  discovery_budget:
    max_minutes: 45
    max_files_to_open: 60
  excluded_paths:
    - "node_modules"
    - ".git"
  requested_goal: ""
  user_or_delegated_approval: ""
```

For `limited_takeover`, create only the context files needed for the affected domain plus `global-capsule.yaml`, `context-index.yaml`, `freshness.yaml`, and evidence. For `full_takeover`, use the canonical `.bagel/agent_context/` tree from `references/governance-data-model.md` plus `.bagel/project_inventory/evidence.md`, `commands.md`, `dependency-map.md`, `test-map.md`, and `open-questions.md`.

## Discovery Passes

Run lightweight, evidence-backed passes:

1. **Structure:** directories, entrypoints, major modules, generated folders to ignore.
2. **Stack:** languages, frameworks, package managers, build tools, runtime targets.
3. **Behavior:** how to run, test, lint, typecheck, preview, or inspect outputs.
4. **Features:** implemented, partial, stubbed, broken, missing.
5. **Conventions:** naming, state/data patterns, styling, architecture boundaries, testing norms.
6. **Integrations:** APIs, databases, auth, external services, credentials needed.
7. **Quality state:** failing tests, broken setup, TODO hotspots, flaky or risky areas.
8. **User intent gaps:** where current implementation and user vision diverge.

Prefer repository evidence: docs, package files, tests, routes, schemas, snapshots, screenshots, commits when available, and actual commands.

## Agent-Facing Context Requirements

Agent-facing files must be:

- short enough to load often,
- factual and cited to files/commands,
- organized by task relevance,
- explicit about what exists already,
- explicit about what must not be duplicated,
- updated after every meaningful change.
- layered for progressive disclosure: global capsule, context index, domain files, task briefs, evidence.

### `project-facts.yaml`

```yaml
project:
  name: "..."
  current_state: blank | partial | production | unknown
  primary_stack: ["..."]
  run_commands:
    dev: "..."
    test: "..."
    lint: "..."
  entrypoints:
    - path: "..."
      purpose: "..."
  constraints:
    - "..."
  evidence_last_updated: "ISO-8601"
```

### `global-capsule.yaml`

Keep this small enough to load in every orchestration cycle. It contains project purpose, current phase, protected intent, protected existing behavior, highest-risk areas, and pointers to deeper context.

### `context-index.yaml`

Map domains/topics to the correct context files, watched paths, owners, and evidence. Workers should use the index to load only relevant details.

### `freshness.yaml`

Track whether each context file is fresh, stale, or disputed. Do not dispatch normal implementation against stale/disputed context.

### `feature-inventory.md`

Use this structure:

```text
Implemented:
- Feature: evidence path/test/route

Partial:
- Feature: what works, what is missing, evidence

Stubbed/Mocked:
- Stub: contract, replacement criterion

Missing:
- Feature: why it matters, related existing modules
```

### `do-not-duplicate.md`

List existing reusable assets:

- components,
- hooks,
- services,
- data models,
- prompts,
- utilities,
- schemas,
- design tokens,
- writing/research structures.

Every implementer should consult this before creating a new abstraction.

## Human Alignment Questions

After project discovery, ask or document:

- Which existing behavior is intentional and must be preserved?
- Which parts are experiments that can be replaced?
- Which rough areas should be improved versus left alone?
- Are current architecture/style choices preferred or accidental?
- What is the user's real goal for the next autonomous run?
- What would count as regression from the user's perspective?

If the user cannot answer, propose defaults and record them in the decision map.

## Update Policy

Update agent-facing context when:

- a module responsibility changes,
- a new convention is introduced,
- a feature moves from partial to implemented,
- tests or commands change,
- a reusable component/service is added,
- a worker discovers a previous fact is wrong.

Workers should return proposed context updates. The orchestrator or Project Cartographer merges them after verification.

Update ownership:

- Project Cartographer owns agent-facing project reality.
- Orchestrator owns dispatch briefs, freshness checks, and final merge of verified updates.
- User Alignment Curator owns human-facing summaries.
- Constitutional Court owns goal/scope conflicts.

Every update should link to an evolution change record.

## Dispatch Rule

For existing projects, workers receive a task-local brief derived from `.bagel/agent_context/`:

```text
Relevant existing modules:
Reuse these:
Do not touch:
Current behavior:
Known risks:
Allowed files:
Verification:
```

Do not give each worker permission to scan the entire repository unless the task is explicitly a discovery task.

## Staleness Detection

Treat agent-facing context as stale when:

- files referenced in it no longer exist,
- tests/commands changed,
- repeated workers contradict it,
- major refactor landed,
- user changes direction.

When stale, pause implementation, run a targeted project-understanding refresh, then continue.

## Progressive Disclosure

Do not load all project understanding into every worker. Use this sequence:

1. Orchestrator reads global capsule and context index.
2. Orchestrator selects relevant domain capsule(s).
3. Orchestrator creates a task brief.
4. Worker reads task brief and assigned files only.
5. Worker reports mismatches or proposed context updates.
6. Project Cartographer verifies and updates authoritative context.
