# Existing Project Understanding Protocol

Use this before BAGEL modifies an existing or partially implemented project. The goal is to understand the current project reality deeply enough that future agents can work without re-exploring the whole codebase each time.

## Core Rule

Do not overwrite the user's existing project mental model with assumptions. Build an evidence-backed model of the current project, compare it with the user's desired direction, then align.

Existing-project understanding is not a one-time scan. It is a living operational model that must be refreshed whenever code, tests, commands, conventions, or user intent change.

## Verify, Don't Trust (mandatory)

**Documentation lies. READMEs drift. `.bagel/` context from a prior run may be wrong.** Every project fact recorded in `.bagel/context.yaml` or `.bagel/agent_context/` must be verified against the live repository — not accepted from a document.

- Every fact cites a real file path, command output, or grep result — never "the README says."
- If a document claims something (e.g. "run `npm test` to test"), **actually run the command** and record the real result. A documented command that fails is recorded as `documented_but_broken`, not as the project's verification method.
- Existing `.bagel/` context is a *hint to re-verify*, not a source of truth. Before relying on a prior context entry, re-verify its key claim against live code. If it cannot be re-verified, mark it `disputed`.

### Multi-Agent Cross-Verification

A single agent reading docs tends to accept them wholesale. To prevent this, the orchestrator dispatches **≥ 2 exploration subagents in parallel** for the discovery pass, each with a different lens and isolated context:

- **structure explorer** — verifies directory structure, entrypoints, module count by `find`/`ls`/reading actual files.
- **behavior explorer** — actually runs build/test/lint/typecheck/dev commands, records real exit codes and output.
- **convention explorer** — verifies naming/state/architecture patterns by `grep` and reading representative modules.
- **surface explorer** — verifies routes/APIs/data contracts by reading the actual route/controller/schema files and counting endpoints.

The Cartographer cross-verifies the explorers' findings against each other. If the structure explorer reports "8 modules" but the behavior explorer's test output references 10, the contradiction must be resolved before context is written. **Do not merge contradictory findings without resolution.**

On platforms without subagent capability, the Cartographer performs these lenses sequentially, but the verification requirement (run commands, read real code) does not weaken — only the parallelism does.

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

In `quick_autonomy`, consolidate the output into `.bagel/context.yaml`:

```yaml
takeover_scope:
  mode: limited_takeover | full_takeover
  target_domains: []
  protected_paths: []
  allowed_paths: []
  excluded_paths: []
project_facts:
  stack: []
  entrypoints: []
  run_commands: {}
  verification_commands: {}
behavior_baseline:
  verified_workflows: []
  known_failures: []
  screenshots_or_snapshots: []
protected_surface:
  user_promises: []
  public_apis: []
  data_contracts: []
  design_language: []
  intentional_flows: []
replaceable_surface:
  accidental_patterns: []
  rough_edges: []
  stale_code: []
do_not_duplicate: []
freshness:
  status: fresh | stale | disputed
  last_checked: "ISO-8601"
  watched_paths: []
open_questions: []
```

## Discovery Passes

Run evidence-backed passes. Keep the scope proportional, but do not skip the domains needed to prevent drift:

1. **Structure:** directories, entrypoints, major modules, generated folders to ignore.
2. **Stack:** languages, frameworks, package managers, build tools, runtime targets.
3. **Behavior:** how to run, test, lint, typecheck, preview, or inspect outputs.
4. **Features:** implemented, partial, stubbed, broken, missing.
5. **Conventions:** naming, state/data patterns, styling, architecture boundaries, testing norms.
6. **Integrations:** APIs, databases, auth, external services, credentials needed.
7. **Quality state:** failing tests, broken setup, TODO hotspots, flaky or risky areas.
8. **User intent gaps:** where current implementation and user vision diverge.
9. **Protected surface:** public APIs, data models, UX flows, brand/taste, user promises, backward compatibility, and production assumptions that should not change accidentally.
10. **Replaceable surface:** rough prototypes, duplicated code, accidental conventions, dead ends, stale experiments, and areas safe to redesign.
11. **Verification baseline:** current command results, visible UI snapshots, benchmark baselines, coverage or smoke checks, and known failing tests.
12. **Dependency and tool map:** normal install/run path, local-only tools, risky upgrades, external services, and unavailable credentials.
13. **Change impact map:** which files or modules are likely affected by the requested goal and which nearby files must be watched for regressions.

Prefer repository evidence: docs, package files, tests, routes, schemas, snapshots, screenshots, commits when available, and actual commands.

**Verification requirement:** every pass above must verify its findings against live code or real command output, not accept documentation claims. Specifically:

- Pass 3 (Behavior): actually run the build/test/lint/typecheck commands. Record real exit codes and output paths. A command documented but not run is not a verified behavior baseline.
- Pass 4 (Features): grep/read actual implementations to confirm what is implemented vs stubbed — do not trust a feature list doc.
- Pass 6 (Integrations): read the actual integration code (API client, DB schema, auth middleware), not just an integrations doc.
- Pass 9 (Protected surface): count actual routes/endpoints by reading the route files, not by trusting an API reference.
- Pass 11 (Verification baseline): this is the most critical — the recorded baseline must come from commands that were actually executed, with output saved to `.bagel/evidence/baseline/`. `not_available` is only acceptable when the command genuinely cannot run (missing runtime, missing credentials); it must never be a shortcut for "I didn't try."

## Baseline Snapshot

Before behavior-changing work, capture enough baseline evidence to prove later that the project improved rather than merely changed:

```yaml
baseline_snapshot:
  created_at: "ISO-8601"
  commands:
    - command: "npm test"
      result: pass | fail | not_available
      evidence: ".bagel/evidence/baseline/npm-test.txt"
  visible_artifacts:
    - path: ".bagel/evidence/baseline/dashboard-desktop.png"
      state: "current dashboard"
  known_failures:
    - id: "KF-001"
      description: ""
      evidence: ""
  green_floors:
    - metric: "e2e_pass_rate"
      value: "current"
      must_not_regress_without_rationale: true
```

If a verifier does not exist, record `not_available` and create the smallest local verifier when it is needed for the current run.

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

## Protected vs Replaceable Draft

The cartographer must draft a protected/replaceable map, then ask the user to veto or correct it using compact choices:

```yaml
protected_replaceable_review:
  protected_by_evidence:
    - item: "Existing API route /api/billing"
      evidence: "tests/billing.test.ts"
      proposed_policy: preserve_contract
  likely_replaceable:
    - item: "Duplicate Button components"
      evidence: "src/components/Button.tsx, src/ui/Button.tsx"
      proposed_policy: consolidate_when_touched
  needs_user_veto:
    - question: "Is the current dashboard layout intentional or just unfinished?"
      options: ["Preserve", "Improve freely", "Only change target module"]
```

The user should not have to explain the whole repo. The system proposes the map from evidence; the user corrects intent.

## Human Alignment Questions

After project discovery, ask or document:

- Which existing behavior is intentional and must be preserved?
- Which parts are experiments that can be replaced?
- Which rough areas should be improved versus left alone?
- Are current architecture/style choices preferred or accidental?
- What is the user's real goal for the next autonomous run?
- What would count as regression from the user's perspective?

If the user cannot answer, propose defaults and record them in the decision map.

Use this prompt shape:

```text
I found these likely protected surfaces: ...
I found these likely replaceable surfaces: ...
Please veto anything wrong. If you do nothing, I will preserve protected surfaces and freely improve replaceable surfaces inside the autonomy contract.
```

## Update Policy

Update agent-facing context when:

- a module responsibility changes,
- a new convention is introduced,
- a feature moves from partial to implemented,
- tests or commands change,
- a reusable component/service is added,
- a worker discovers a previous fact is wrong.
- a progress delta is backward or three deltas are lateral,
- a reviewer finds drift caused by stale project understanding,
- baseline or final-diff evidence contradicts the context model,
- the user corrects a protected/replaceable classification.

Workers should return proposed context updates. The orchestrator or Project Cartographer merges them after verification.

Update ownership:

- Project Cartographer owns agent-facing project reality.
- Orchestrator owns dispatch briefs, freshness checks, and final merge of verified updates.
- User Alignment Curator owns human-facing summaries.
- Constitutional Court owns goal/scope conflicts.

Every update should link to an evolution change record.

## Continuous Refresh Loop

At the end of every meaningful cycle:

1. Check whether changed files intersect `freshness.watched_paths`.
2. If yes, update the relevant section of `.bagel/context.yaml` or the domain capsule.
3. If a worker reports "this context is wrong," mark it `disputed` immediately and dispatch a targeted cartographer refresh before more work in that area.
4. If a new reusable component/service/prompt/schema was created, add it to `do_not_duplicate`.
5. If behavior changed, update `behavior_baseline` and the user-facing `current-project-reality.md`.
6. If the user changes direction, compare it against protected surfaces and update the decision map before implementation.

Do not let a long run continue on stale project facts simply because the original intake was good.

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
