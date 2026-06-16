# BAGEL Genesis

> A long-run autonomy protocol for Claude Code and Codex: align deeply, bind a real loop, dispatch clean-context agents, keep improving until the agreed iteration/budget boundary.

**English** | [简体中文](README.zh-CN.md)

---

## Why This Exists

Normal agent usage is already powerful, but it often fails in exactly the places that matter for overnight work:

- it asks a few shallow planning questions, then starts with an under-specified goal;
- it stops at routine friction instead of solving it;
- the main context gets polluted by implementation/debug details;
- the same agent implements, judges, and declares victory;
- it treats "all requested features are done" as final completion instead of the first iteration;
- it reports progress that is hard to verify the next morning.

**BAGEL Genesis turns that into a governed autonomous loop.** It makes the agent first clarify the user's real goal, taste, hard-stops, budget, runtime mode, and evaluation criteria; then it keeps running through implementation, review, recovery, bar-raising, and the next iteration.

The key idea is simple:

```text
Deep Align -> Bind Loop -> Build -> Verify -> Raise the Bar -> Iterate Again
```

The run stops only when the user-set iteration/budget boundary is reached, the user stops it, token/runtime capacity is exhausted with a checkpoint, or a true hard-stop is hit.

## What Makes It Different

| Problem | BAGEL's answer |
|---|---|
| Shallow upfront planning | Depth-floored alignment: snap / standard / deep, with persisted decisions |
| "Come back later" idle stops | Mandatory loop/timer binding, interval <= 25 minutes |
| Context pollution | Main model is Orchestrator; implementation, runtime debugging, evaluation, review, and taste judgment are dispatched |
| Agent self-approval | Review independence is derived from agent/session registry, not self-claimed |
| Weak taste and local optimization | Product Visionary, Brainstormers, and Judgment Council for direction-level decisions |
| No clear quality bar | Evaluation Architect generates task-specific metrics, rubrics, completion rules, and anti-gaming notes |
| "Initial goals done" = final | Iteration Contract: initial goals complete one iteration; next target set must be raised if budget remains |
| Repeating the same failure | Lesson memory promotes recovery into reusable gotchas and playbooks |
| Fake progress | `bagel_run_check.py`, `flywheel_check.py`, and `bagel_memory_check.py` mechanically validate the run state |

## When To Use It

Use BAGEL when you want Claude Code or Codex to:

- build or significantly improve an app, website, tool, game, research artifact, writing project, or data analysis;
- take over an existing project without drifting from its real architecture and behavior;
- run unattended for hours while continuing to make useful progress;
- generate stronger goals after completing the obvious ones;
- create missing tests, verifiers, screenshots, benchmarks, setup scripts, or experiment harnesses;
- return a morning briefing with concrete before/after evidence.

Do not use it for tiny scripts, narrow bug fixes, or one-shot answers.

## Mental Model

BAGEL separates the work into a control plane and a deliverable plane.

- **Control plane:** `.bagel/` state, constitution, alignment decisions, task queue, evidence, reviews, lessons, STATUS.
- **Deliverable plane:** the actual app, experiment, paper, site, or artifact the user asked for.

`.bagel/` is not the deliverable. It exists so the agent can run for a long time without losing alignment or corrupting context.

The main model becomes the **Orchestrator**. It does not write product code when subagents are available. It dispatches specialized agents:

- **Project Cartographer:** verifies the existing project from real files and commands.
- **Evaluation Architect:** creates the evaluation system for each iteration.
- **Implementer / Skeleton Builder:** performs bounded code or artifact work.
- **Runtime Doctor:** fixes environment, dependency, build/test, browser, screenshot, or verifier failures.
- **Reviewers / Red-Team:** inspect changes independently.
- **Product Visionary / Brainstormers:** generate higher-value and more novel directions.
- **Judgment Council:** selects tasteful, coherent directions and can veto polished-but-wrong ideas.
- **User Alignment Curator:** maintains the human briefing and optional HTML dashboard.

## Quick Start

Install or copy the skill folder so Claude Code/Codex can load:

```text
bagel-genesis/
├── SKILL.md
├── agents/
├── references/
├── scripts/
└── evals/
```

Then ask your agent to use BAGEL for a long-running task:

```text
Use BAGEL Genesis. I want to align deeply first, then run autonomous iteration.
Bind a loop/timer no longer than 25 minutes, initialize git if needed, and keep going
until the agreed iteration budget is reached or a true hard-stop occurs.
```

For an existing project:

```text
Use BAGEL Genesis to take over this project. First verify the repo reality from files
and commands, draft protected vs replaceable surfaces, ask me only for intent/taste/
hard-stop decisions, then run autonomous iterations.
```

For research or experiments:

```text
Use BAGEL Genesis for an autonomous research run. Align on the hypothesis, evaluation
method, budget, and hard-stops; build or repair the benchmark harness; run experiments;
record lessons; and iterate on better hypotheses when results stall.
```

## Configuration Decisions BAGEL Should Capture

At alignment, the agent should persist these choices:

- `alignment_depth`: `snap_alignment` / `standard_alignment` / `deep_alignment`
- `execution_strategy`: `stable_long_run` / `balanced_parallel` / `fast_parallel`
- `stop_contract`: max iterations, target iterations, time/token budget, hard-stops
- `autonomy_contract`: what the agent may decide alone
- `taste_kernel`: exemplars, style, product identity, quality expectations
- `innovation_contract`: execution excellence / differentiated / breakthrough
- `evaluation`: metrics, rubrics, completion rule, anti-gaming notes
- `loop_binding`: actual timer/scheduler proof, interval <= 25 minutes
- `git`: baseline commit and rollback strategy

## Runtime Checks

Run these from the repository root that contains `.bagel/`:

```bash
python bagel-genesis/scripts/bagel_run_check.py /path/to/project
python bagel-genesis/scripts/flywheel_check.py /path/to/project
python bagel-genesis/scripts/bagel_memory_check.py /path/to/project
python bagel-genesis/scripts/skill_lint.py bagel-genesis
```

What they catch:

- missing git rollback or loop/timer proof;
- missing agent dispatch records;
- control-plane work mistaken as product work;
- Build/iteration without an evaluation spec;
- fake or missing evidence files;
- false independent review claims;
- regressions below prior green floors;
- bar raises without brainstormers or Judgment Council;
- complete status before `iterations_completed >= max_iterations`;
- recovery-heavy runs that learned no reusable lessons.

## Current Contents

```text
bagel-genesis/
├── SKILL.md
├── agents/          # 19 role prompts
├── references/      # 38 trigger-loaded protocols
├── scripts/         # 5 validators/helpers
└── evals/           # 61 behavior evals
```

## Status

Current version: **v1.5**.

Validated locally:

- skill metadata validation passes;
- BAGEL consistency lint passes;
- evals JSON is valid and sequential;
- targeted runtime checks catch the latest real-world failures around control-plane confusion, missing evaluation specs, premature completion, and Orchestrator context pollution.

## Honest Boundaries

BAGEL improves the odds of high-quality autonomous work; it does not make model limits disappear.

- It can run computational experiments, benchmarks, app builds, UI polish, writing, and project optimization.
- It cannot verify physical-world claims without an authorized evidence pipeline.
- It should stop for irreversible destructive actions, production data/infrastructure, credentials, paid resources, serious security/privacy/legal/financial risk, or core identity changes.

## License

MIT
