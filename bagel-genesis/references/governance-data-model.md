# Governance Data Model

Use when creating, updating, or validating `.bagel/` state. The goal is one canonical truth model per run, not scattered memory.

## Canonical Sources

In `quick_autonomy`, the canonical sources are consolidated:

| Domain | Canonical File | Notes |
|---|---|---|
| Run state, tasks, gates, progress, budget | `.bagel/state.yaml` | Single operational control plane |
| User intent, autonomy, horizons, taste | `.bagel/constitution.yaml` | Stable promise and stop/continue policy |
| Existing project truth | `.bagel/context.yaml` | Only required when modifying an existing project |
| Decisions, recovery, evolution, user decisions | `.bagel/ledger.yaml` | Append concise records or expand to directories when needed |
| Progress deltas | `.bagel/evidence/progress-deltas.yaml` | Objective cycle-by-cycle evidence |
| Bar raises | `.bagel/evidence/bar-raises.yaml` | Raised standards and why they are valuable |
| Innovation candidates | `.bagel/innovation/ledger.yaml` | Novel concepts, probes, and adopt/park/reject decisions |
| Lesson memory | `.bagel/ledger.yaml#lessons` or `.bagel/lessons/*` | Reusable gotchas, recovery lessons, and playbooks |
| Loop binding and telemetry | `.bagel/state.yaml.loop_binding`, `.bagel/state.yaml.telemetry` | Timer/scheduler proof and runtime counters |
| Review registry | `.bagel/state.yaml.review_registry` | Derived review independence levels in quick mode |
| Flywheel integrity | `.bagel/state.yaml.gates.flywheel_integrity_passed` | Latest `scripts/flywheel_check.py` result |
| Human status entry | `.bagel/STATUS.md` | Single user-readable status entry point |
| HTML briefing | `.bagel/user_briefing/alignment-dashboard.html` | Optional visual dashboard generated from canonical state |

In `full_genesis`, these domains may expand to specialized files:

| Domain | Canonical File | Notes |
|---|---|---|
| Runtime capability | `.bagel/runtime_capabilities.yaml` | What the platform can actually do |
| Artifact profile | `.bagel/artifact_profile.yaml` | Which gates apply |
| User intent | `.bagel/constitution.json` | Stable promise and boundaries |
| Human decisions | `.bagel/alignment/human-decisions.yaml` | Approval/delegation/assumption state |
| Current state | `.bagel/state.json` | Current BAGEL state and stop semantics |
| Tasks | `.bagel/task_queue.json` | Pending/running/done/blocked units |
| Progress | `.bagel/progress.json` | Last verified progress and next action |
| Gates | `.bagel/gates/status.yaml` | Predicate results |
| Amendment history | `.bagel/ledger/amendment-history.yaml` | Court verdict counts and rationale classes |
| Existing project truth | `.bagel/agent_context/*` | Evidence-backed worker context |
| Change history | `.bagel/evolution/*` | Audit, rollback, rationale |
| Git/agents | `.bagel/git/*`, `.bagel/agents/*` | Ownership and integration state |
| Flywheel evidence | `.bagel/evidence/*` | Progress deltas, bar raises, command output, screenshots, benchmarks |
| Innovation ledger | `.bagel/innovation/ledger.yaml` | Divergent concept candidates and probe evidence |
| Lesson memory | `.bagel/lessons/*` | Cross-run operational wisdom and reusable playbooks |
| Loop binding and telemetry | `.bagel/state.json` or `.bagel/progress.json` | Timer/scheduler proof and runtime counters |
| Human status entry | `.bagel/STATUS.md` | Single user-readable status entry point |
| HTML briefing | `.bagel/user_briefing/alignment-dashboard.html` | Optional visual dashboard generated from canonical state |

UPMG is optional. If used, it is the graph backend for complex software/product runs. If not used, `.bagel/product_graph.yaml` plus the files above are canonical.

## Canonical Directory Trees

This file is the authority for `.bagel/` tree names. Other references may explain how to write these files, but must not define competing names.

Agent-facing context:

```text
.bagel/agent_context/
├── global-capsule.yaml
├── context-index.yaml
├── freshness.yaml
├── project-facts.yaml
├── conventions.md
├── module-map.md
├── feature-inventory.md
├── current-behavior.md
├── do-not-duplicate.md
├── known-risks.yaml
├── task-brief-template.md
├── domains/
│   └── <domain>.md
├── task-briefs/
│   └── <task-id>.md
└── evidence-links/
```

Human-facing briefing:

```text
.bagel/
├── STATUS.md
└── user_briefing/
    ├── README.md
    ├── quick-status.md
    ├── alignment-dashboard.html
    ├── decision-dashboard.md
    ├── current-project-reality.md
    ├── architecture-or-structure.md
    ├── quality-and-risks.md
    ├── progress-timeline.md
    ├── evolution-summary.md
    └── deep-dives/
        └── <topic>.md
```

Innovation and lesson memory:

```text
.bagel/
├── innovation/
│   └── ledger.yaml
└── lessons/
    ├── index.yaml
    ├── gotchas.yaml
    ├── environment.yaml
    ├── engineering.yaml
    ├── product.yaml
    ├── research.yaml
    └── playbooks/
        └── <slug>.md
```

`.bagel/STATUS.md` is the single entry point for humans after a long run. It summarizes phase, last verified progress, autonomy safety, current blockers, next action, and links to deeper files. In quick mode it is generated from `state.yaml`, `constitution.yaml`, `context.yaml`, `ledger.yaml`, and `evidence/progress-deltas.yaml`. In full mode it may also draw from `state.json`, `progress.json`, `gates/status.yaml`, `task_queue.json`, `human-decisions.yaml`, and `user_briefing/*`. If canonical files disagree, `STATUS.md` must say "state conflict" and link to the conflict report instead of choosing silently.

## Schema Registry

Create `.bagel/schema-registry.yaml`:

```yaml
schemas:
  quick_state: {path: ".bagel/state.yaml", format: yaml, required_for_quick_autonomy: true}
  quick_constitution: {path: ".bagel/constitution.yaml", format: yaml, required_for_quick_autonomy: true}
  quick_context: {path: ".bagel/context.yaml", format: yaml, required_for_existing_project_quick_autonomy: true}
  quick_ledger: {path: ".bagel/ledger.yaml", format: yaml, required_for_quick_autonomy: true}
  progress_deltas: {path: ".bagel/evidence/progress-deltas.yaml", format: yaml, required_for_long_run: true}
  bar_raises: {path: ".bagel/evidence/bar-raises.yaml", format: yaml, required_for_excellence_loop: true}
  innovation_ledger: {path: ".bagel/innovation/ledger.yaml", format: yaml, required_when_innovation_contract_is_differentiated_or_breakthrough: true}
  lesson_memory: {path: ".bagel/lessons/index.yaml", format: yaml, required_after_recovery_or_repeated_failure: true, optional_in_quick: "store inside ledger.yaml#lessons"}
  loop_binding: {path: ".bagel/state.yaml#loop_binding", format: yaml, required_for_autonomous_iteration: true}
  telemetry: {path: ".bagel/state.yaml#telemetry", format: yaml, required_for_long_run: true}
  html_dashboard: {path: ".bagel/user_briefing/alignment-dashboard.html", format: html, optional: true}
  flywheel_integrity: {path: ".bagel/state.yaml#gates.flywheel_integrity_passed", format: yaml, required_for_long_run: true}
  quick_review_registry: {path: ".bagel/state.yaml#review_registry", format: yaml, required_when_reviews_claim_independence: true}
  # Full-genesis detailed files. Quick mode stores equivalents inside state.yaml/constitution.yaml/ledger.yaml.
  constitution_full: {path: ".bagel/constitution.json", format: json, required_for_full_genesis: true}
  completion_horizon: {path: ".bagel/completion_horizon.yaml", format: yaml, required_for_full_genesis: true, optional_in_quick: "store inside constitution.yaml"}
  runtime_capabilities: {path: ".bagel/runtime_capabilities.yaml", format: yaml, required_for_long_run: true}
  artifact_profile: {path: ".bagel/artifact_profile.yaml", format: yaml, required_for_full_genesis: true, optional_in_quick: "store inside state.yaml"}
  run_mode: {path: ".bagel/run_mode.yaml", format: yaml, required_for_full_genesis: true, optional_in_quick: "store inside state.yaml"}
  run_budget: {path: ".bagel/run_budget.yaml", format: yaml, required_for_long_run: true, optional_in_quick: "store inside state.yaml"}
  context_policy: {path: ".bagel/context_policy.yaml", format: yaml, required_for_full_genesis: true}
  human_decisions: {path: ".bagel/alignment/human-decisions.yaml", format: yaml, required_for_full_genesis: true, optional_in_quick: "store inside ledger.yaml"}
  gate_status_full: {path: ".bagel/gates/status.yaml", format: yaml, required_for_full_genesis: true, optional_in_quick: "store inside state.yaml under gates:"}
  state_full: {path: ".bagel/state.json", format: json, required_for_full_genesis: true}
  progress_full: {path: ".bagel/progress.json", format: json, required_for_full_genesis: true, optional_in_quick: "store inside state.yaml"}
  task_queue_full: {path: ".bagel/task_queue.json", format: json, required_for_full_genesis: true, optional_in_quick: "store inside state.yaml"}
  amendment_history: {path: ".bagel/ledger/amendment-history.yaml", format: yaml, required_when_court_active: true}
  human_status: {path: ".bagel/STATUS.md", format: markdown, required_for_long_run: true}
  project_context_freshness: {path: ".bagel/agent_context/freshness.yaml", format: yaml, required_for_existing_project: true}
  project_context_index: {path: ".bagel/agent_context/context-index.yaml", format: yaml, required_for_existing_project: true}
  evolution_index: {path: ".bagel/evolution/index.yaml", format: yaml, required_for_meaningful_changes: true}
  git_branches: {path: ".bagel/git/branches.yaml", format: yaml, required_for_git_work: true}
  git_locks: {path: ".bagel/git/locks.yaml", format: yaml, required_for_parallel_work: true}
  git_merge_queue: {path: ".bagel/git/merge-queue.yaml", format: yaml, required_for_git_work: true}
  agent_registry: {path: ".bagel/agents/registry.yaml", format: yaml, required_for_multi_agent: true}
```

## Minimum Shape Checklist

Run `scripts/skill_lint.py` when editing the BAGEL skill itself. When no project-specific validator exists for a BAGEL run, validate these fields manually and record the result in `.bagel/evidence/schema-validation.md`:

```yaml
validation:
  checked_at: "ISO-8601"
  checked_by: "orchestrator"
  files:
    - path: ".bagel/state.json"
      result: pass | fail
      required_fields: ["state", "stop_semantics", "current_task", "next_action"]
    - path: ".bagel/progress.json"
      result: pass | fail
      required_fields: ["last_verified_step", "completed_tasks", "open_risks", "next_action"]
    - path: ".bagel/task_queue.json"
      result: pass | fail
      required_fields: ["tasks[].id", "tasks[].status", "tasks[].acceptance_criteria"]
    - path: ".bagel/gates/status.yaml"
      result: pass | fail
      required_fields: ["gates[].id", "gates[].status", "gates[].evidence", "gates[].checked_at"]
    - path: ".bagel/alignment/human-decisions.yaml"
      result: pass | fail
      required_fields: ["decisions[].id", "decisions[].status", "decisions[].source", "decisions[].decision"]
    - path: ".bagel/ledger/amendment-history.yaml"
      result: pass | fail | not_applicable
      required_fields: ["verdict_counts", "rationale_classes[].class", "rationale_classes[].count", "rationale_classes[].recent_examples"]
    - path: ".bagel/git/locks.yaml"
      result: pass | fail | not_applicable
      required_fields: ["locks[].id", "locks[].owner", "locks[].paths", "locks[].status", "locks[].heartbeat_at"]
```

Validation fails if a required canonical file is missing, malformed, stale, or lacks evidence for its current status. Missing validators do not waive validation; they switch to the manual checklist.

## Consistency Checks

Before state transition, merge, resume, or final delivery, check:

- every active task has a gate status or planned gate check,
- every meaningful change has an evolution record,
- every human-sensitive decision links to `human-decisions.yaml`,
- every worker dispatch cites context capsule versions,
- every active lock has a live agent registry entry,
- every completed task has verification evidence,
- every stale/disputed context file blocks normal implementation until refreshed,
- every waiver links to human approval or autonomy-contract authority.
- `.bagel/STATUS.md` is updated after every milestone, stop, resume, recovery, or final delivery.

## Human Decisions

Use `.bagel/alignment/human-decisions.yaml`:

```yaml
decisions:
  - id: "HD-001"
    topic: "Autonomous dependency upgrades"
    status: approved | delegated | assumed_default | blocked | rejected
    source: user_explicit | autonomy_contract | system_default
    decision: "Do not upgrade major dependencies unattended."
    applies_to:
      - "dependency/toolchain changes"
    evidence:
      - ".bagel/alignment/autonomy-contract.yaml"
    expires_or_revisit: "optional"
```

`assumed_default` decisions are weaker than `approved`; they must be visible in user briefing and can be overridden by later user instructions.

## Update Rules

- Orchestrator may update canonical state, gates, progress, queues, ledgers, and merge metadata.
- Project Cartographer owns agent-facing project truth, but Orchestrator may merge verified context updates.
- User Alignment Curator owns human-facing summaries.
- Workers propose updates; they do not silently mutate canonical governance state unless assigned that exact task.
- Every canonical update links to evidence or an evolution record.
