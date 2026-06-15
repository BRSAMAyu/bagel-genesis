# BAGEL Genesis

> Deep upfront alignment + long-running autonomous iteration for Claude Code, Codex, and similar agentic coding systems.

BAGEL Genesis is a skill-level operating protocol for turning a vague vision or a partially built project into a finished, high-quality deliverable. It is designed for the common workflow where you align with an agent before bed, delegate a difficult task, and expect the system to keep working instead of stopping at the first ambiguity.

It is not a single mega-prompt. It is a structured skill with:

- an entry point: [`SKILL.md`](SKILL.md)
- role prompts in [`agents/`](agents/)
- trigger-loaded protocols in [`references/`](references/)
- validation and runtime helper scripts in [`scripts/`](scripts/)
- behavior evals in [`evals/evals.json`](evals/evals.json)

## What BAGEL Is For

Use BAGEL when you want an agent to:

- clarify a fuzzy product, research, writing, or optimization goal before execution
- take over an existing project without drifting away from its real architecture and conventions
- run for hours through implementation, verification, review, recovery, and polish
- keep making measurable progress instead of waiting for routine approval
- create missing local tools, tests, screenshots, benchmarks, and verifiers when needed
- return a readable morning briefing that explains what happened, what changed, and what still needs a decision

Do not use BAGEL for trivial scripts, tiny code edits, narrowly specified tickets, or tasks where you want a quick one-shot answer.

## Core Idea

BAGEL has three phases:

```text
Align  ->  Build  ->  Polish
```

- **Align:** make the user's intent, hard boundaries, runtime strategy, and quality bar executable.
- **Build:** implement one bounded slice at a time, verify it, record objective progress, and continue.
- **Polish:** critique, improve, verify, raise the bar, and stop only when further work has low expected value or the agreed budget is exhausted.

After the user delegates autonomous work, BAGEL's tie-breaker is:

> If a rule, review, failed attempt, missing tool, or platform limitation makes the agent want to stop and ask the user, continue instead unless the situation hits a true hard-stop boundary.

Hard-stops are intentionally narrow: irreversible or non-recoverable destructive action, serious security/privacy/legal/financial/production-data risk, credentials or paid external resources, core product/research identity changes, or an explicit user-forbidden boundary.

## Key Features

### Deep Alignment Before Autonomy

BAGEL avoids shallow "plan mode" alignment. It asks decision-oriented questions and persists the answers into `.bagel/` state.

Alignment supports three depths:

| Depth | Use when | Behavior |
|---|---|---|
| `snap_alignment` | urgent or low-stakes | capture essentials, default reversible details, start quickly |
| `standard_alignment` | default | ask key choice cards plus the most relevant open questions |
| `deep_alignment` | important, ambiguous, high-budget | keep asking decision points until the user's mental model is clear enough |

Choice cards cover autonomy level, execution strategy, run budget, takeover aggressiveness, taste source, research verification, hard-stop boundaries, and HTML briefing preferences.

### Three Execution Strategies

| Strategy | Use when | Behavior |
|---|---|---|
| `stable_long_run` | overnight / unattended work | lower write parallelism, stronger verification, continuous cycles |
| `balanced_parallel` | speed and reliability both matter | moderate concurrency and review depth |
| `fast_parallel` | user is nearby and rollback is cheap | faster exploration, more aggressive parallelism |

### Runtime Loop and Timer Binding

When the user says "start autonomous iteration," BAGEL should not park in planning-only mode. It must bind to the strongest available runtime:

- `scheduled_resume`: platform automation, scheduled task, or timer
- `external_harness`: cron, launchd, cloud task, CLI loop, or other harness
- `active_session_loop`: current platform loop is actively running
- `degraded_resume`: every native loop mechanism was proven unavailable, so unattended continuation is not guaranteed (STATUS `[DEGRADED]`)

Loop state records trigger interval, next wake time, schedule proof, resume command, and telemetry.

### Objective Progress Signals

Every cycle appends to:

```text
.bagel/evidence/progress-deltas.yaml
```

Each delta is classified as:

- `forward`: measurable improvement or closed risk
- `lateral`: activity without measurable progress
- `backward`: regression, new blocker, degraded metric, or worse artifact state

Three consecutive lateral cycles force a strategy switch. Backward cycles require repair, rollback, or isolation before unrelated polish.

### Existing Project Takeover

For existing projects, BAGEL does not ask the user to explain facts the repository can reveal. It runs a Project Cartographer pass and drafts:

- current stack, entrypoints, run commands, verification commands
- behavior baseline and known failures
- protected surfaces: public APIs, data contracts, user-visible flows, design language, user promises
- replaceable surfaces: rough prototypes, duplicated abstractions, accidental conventions, stale experiments
- reusable assets that must not be duplicated
- watched paths and context freshness

The user can veto or correct the draft instead of reconstructing the whole project from memory.

### Human-Readable Briefing

BAGEL maintains:

```text
.bagel/STATUS.md
.bagel/user_briefing/
```

Optional HTML dashboard support is defined in [`references/alignment-dashboard-html.md`](references/alignment-dashboard-html.md). The dashboard is a continuous, high-density visual summary of alignment, project reality, runtime state, risks, progress, and morning review items.

## Repository Layout

```text
bagel-genesis/
├── SKILL.md
├── README.md
├── agents/
│   ├── orchestrator.md
│   ├── implementer.md
│   ├── project-cartographer.md
│   ├── independent-reviewer.md
│   └── ...
├── references/
│   ├── alignment-protocol.md
│   ├── project-understanding.md
│   ├── loop-runtime.md
│   ├── runtime-capabilities.md
│   ├── platform-codex.md
│   ├── platform-claude-code.md
│   ├── excellence-loop.md
│   ├── recovery-protocol.md
│   ├── alignment-dashboard-html.md
│   └── ...
├── scripts/
│   ├── detect_runtime_capabilities.py
│   ├── bagel_run_check.py
│   ├── flywheel_check.py
│   └── skill_lint.py
└── evals/
    └── evals.json
```

## Installation

### Codex

Clone this repository or copy the `bagel-genesis/` folder into your Codex skills directory.

Common local install:

```bash
mkdir -p ~/.codex/skills
cp -R bagel-genesis ~/.codex/skills/
```

Then start a Codex session and ask for BAGEL by name, for example:

```text
Use the bagel-genesis skill. I want to align on this product idea, then run stable long-run autonomous iteration overnight.
```

### Claude Code

Clone this repository somewhere Claude Code can read it, then reference the skill in your project instructions or ask Claude Code to use the `bagel-genesis` skill folder directly.

Example prompt:

```text
Use /path/to/bagel-genesis as the BAGEL Genesis skill. First run deep alignment, then start stable long-run autonomous iteration. Do not remain in planning-only mode after alignment.
```

For long unattended work, configure Claude Code's available loop/scheduled-task mechanism, or let BAGEL detect and record whether only manual resume is available.

### GitHub Source Install

```bash
git clone https://github.com/BRSAMAyu/bagel-genesis.git
```

Then copy or symlink the `bagel-genesis` directory into the skill location used by your agent platform.

## Quick Start

### Blank-Slate Product

```text
Use bagel-genesis.

I want to build a polished app from this rough idea:
...

Start with standard alignment. Then use stable_long_run autonomous iteration for up to 12 cycles, checkpoint every 30 minutes, and wake me only for true hard-stops.
```

### Existing Project Takeover

```text
Use bagel-genesis.

This repo is an existing product. First run Project Cartographer to understand what exists, what must be preserved, and what can be redesigned. Then ask me to veto the protected/replaceable draft. After that, run stable_long_run polish and implementation.
```

### Research or Optimization Run

```text
Use bagel-genesis.

I want an autonomous experiment loop. Align on the benchmark, baseline, and stop criteria. If the first approach stalls, generate alternative hypotheses and keep testing. Record progress deltas and preserve all evidence.
```

## Runtime Configuration

Before promising autonomous continuation, BAGEL should run:

```bash
python scripts/detect_runtime_capabilities.py --out .bagel/runtime_capabilities.yaml
```

This detects platform clues, CLI tools, scheduler availability, Git support, browser/visual-check support, and local tool-provisioning capability. The agent then maps those facts to one of:

- `single_session`
- `degraded_resume`
- `scheduled_resume`
- `external_harness`

For explicit autonomous iteration, BAGEL must record a loop binding:

```yaml
loop_binding:
  mode: scheduled_resume | external_harness | active_session_loop | degraded_resume   # <= 25 min
  platform: codex | claude_code | other
  schedule_id: ""
  trigger_interval_minutes: 10
  next_wakeup_at: "ISO-8601"
  resume_command_or_action: ""
  proof:
    - "automation id, cron entry, scheduled task, active /loop config, or harness command"
```

If the result is `degraded_resume`, the agent must not claim it will continue unattended and STATUS.md is marked `[DEGRADED]`.

## `.bagel/` Runtime State

BAGEL writes project-local durable state under `.bagel/`. This directory is runtime state and should usually be ignored by Git.

Quick mode uses a compact control plane:

```text
.bagel/
├── state.yaml
├── constitution.yaml
├── context.yaml
├── ledger.yaml
├── STATUS.md
├── evidence/
│   ├── progress-deltas.yaml
│   └── bar-raises.yaml
└── user_briefing/
    └── alignment-dashboard.html
```

Full mode expands into detailed files for broad, high-risk, multi-day, or parallel work.

## Validation

Validate the skill itself:

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py /path/to/bagel-genesis
python /path/to/bagel-genesis/scripts/skill_lint.py /path/to/bagel-genesis
python3 -m json.tool /path/to/bagel-genesis/evals/evals.json >/dev/null
```

Validate a BAGEL run's operational substrate and flywheel evidence:

```bash
python /path/to/bagel-genesis/scripts/bagel_run_check.py /path/to/project
python /path/to/bagel-genesis/scripts/flywheel_check.py /path/to/project
```

`bagel_run_check.py` verifies that the real `.bagel/` run has git rollback, loop binding, <=25 minute wake interval, alignment floors, agent dispatch records, implementer/reviewer separation, STATUS sections, and HTML dashboard ownership.

`flywheel_check.py` verifies evidence paths, green-floor regressions, review-level claims, bar-raise value classes, stuck metrics, budget monotonicity, and other failure modes that can make a long run look productive when it is not.

## Safety Model

BAGEL is autonomy-first, but not reckless. It should continue through ordinary friction:

- missing tests or verifiers
- broken local setup
- failing experiments
- UI quality gaps
- review failures
- temporary blocked lanes
- need for local scripts, screenshots, benchmarks, or harnesses

It should stop or wake the user only for true hard-stops:

- irreversible or non-recoverable destructive action
- production data or production infrastructure changes
- credentials, tokens, paid accounts, or paid services
- serious security, privacy, legal, or financial risk
- core product/research identity changes
- explicit user-forbidden boundaries

## Current Status

BAGEL Genesis v1 is documentation-complete and internally validated:

- skill metadata validation passes
- BAGEL consistency lint passes
- evals JSON is valid and sequential
- 47 behavior evals cover alignment depth floors, project takeover, mandatory loop/git/dispatch, context isolation, brainstormer diversity, verify-dont-trust exploration, immediate loop binding, pointer-only wake prompts, runtime effectiveness audit, loop binding, recovery, flywheel integrity, visual evidence, and HTML briefing

The remaining proof is empirical: run it on real projects overnight and compare the results against ordinary agent use.

## License

MIT
