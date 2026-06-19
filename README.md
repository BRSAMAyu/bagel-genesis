<div align="center">

# 🥯 BAGEL Genesis

**Turn a vague vision into a finished, high-quality deliverable — while you sleep.**

A skill-level operating protocol for autonomous multi-agent project delivery on Claude Code and Codex.

**English** | [简体中文](README.zh-CN.md)

</div>

---

[![Skills Standard](https://img.shields.io/badge/Agent%20Skills-Standard-blue)](https://skills.sh)
[![Version](https://img.shields.io/badge/version-v5.0-green)](#changelog)
[![Evals](https://img.shields.io/badge/evals-120-orange)](bagel-genesis/evals/evals.json)
[![Darwin](https://img.shields.io/badge/Darwin-9%20agent%20audit-blueviolet)](#changelog)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

## What is this?

BAGEL Genesis is a **skill** — a markdown protocol that an AI coding agent loads and follows. It governs long-running, autonomous, multi-agent work: the kind where you delegate a build overnight and expect coherent, verified progress by morning.

The core loop is simple:

```text
Align (deeply) → Build (with evidence) → Iterate (raise the bar) → Polish (to excellence)
```

The run stops only at the user-set iteration/budget boundary, a user stop, capacity exhaustion with checkpoint, or a true hard-stop.

## Why it exists

Normal agent usage fails in exactly the places that matter for unattended work:

- shallow planning questions → under-specified goal
- stops at routine friction instead of solving it
- context polluted by debug details
- same agent implements, reviews, and declares victory
- "all features done" treated as final completion
- progress that's hard to verify the next morning

**BAGEL turns this into a measured expert-autonomy runtime** with mechanical checks that progress is real.

## Key features

| Problem | BAGEL's answer |
|---|---|
| Shallow upfront planning | Depth-floored alignment (snap/standard/deep) with persisted decisions |
| "Come back later" idle stops | Mandatory loop/timer binding, ≤25 min interval |
| Context pollution | Supervisor/Orchestrator/worker separation; replace-not-compact |
| Agent self-approval | Review independence from agent/session registry |
| Weak taste / local optimization | Brainstormers + Judgment Council for direction-level decisions |
| No clear quality bar | Evaluation Architect generates metrics, rubrics, anti-gaming notes |
| Fake progress | 26 mechanical validators replay evidence, check hashes, enforce regression floors |
| Silent scope creep | Scope deltas track allowed/touched paths with git-diff-derived coverage |
| Unverifiable claims | Statistical-rigor gate (n_seeds, p_value < threshold, effect size, correction) |
| Fabricated evidence | `--replay` re-executes cited commands by default |
| Hardcoded secrets in output | `no_hardcoded_secrets` gate fails unconditionally |
| Emergency stop ignored | Circuit-breaker `stop_gate` HALTs the suite (not a repairable failure) |

## Architecture

```text
User intent
    ↓
Supervisor (root model) — arbitrate hard-stops, heartbeat, respawn
    ↓
Orchestrator (internal) — dispatch bounded work, manage state
    ↓
Workers — Implementer, Runtime Doctor, Reviewers, Evaluation Architect,
          Security Engineer, Product Visionary, Red-Team Oracle, ...
```

**Control plane** (`.bagel/`) vs **deliverable plane** (the actual artifact) are strictly separated. The control plane exists so the agent can run for hours without losing alignment or corrupting context.

## Quick start

Install the skill folder so Claude Code/Codex can load it:

```text
bagel-genesis/
├── SKILL.md          # the core protocol
├── agents/           # 27 role prompts
├── references/       # 65 trigger-loaded protocols + 6 expert packs
├── scripts/          # 26 mechanical validators
└── evals/            # 120 behavior evals + dry-run results
```

Then ask your agent:

```text
Use BAGEL Genesis. I want to align deeply first, then run autonomous iteration.
Bind a loop/timer no longer than 25 minutes, initialize git if needed,
and keep going until the agreed iteration budget is reached or a true hard-stop occurs.
```

## Mechanical validators (the anti-cheat layer)

BAGEL ships 26 Python validators that the agent runs each cycle. Key ones:

- **`bagel_v3_check.py`** — unified suite runner (26 checks + emergency-stop circuit breaker)
- **`expert_strategy_check.py`** — requirement coherence, premise falsifiability, statistical rigor, claim-evidence matrix, council output validation, named-dependency protocol, dataset integrity
- **`flywheel_check.py`** — regression floors (with provenance), evidence content (≥50 bytes), iteration/cycle/budget caps
- **`scope_check.py`** — git-diff-derived scope coverage (omission = fail), Constitutional Court verdict verification
- **`production_surface_check.py`** — inline-secret scan (unconditional fail), production-connection detection
- **`evaluation_quality_check.py`** — gameable-metric pairing (metric_role mandatory + role↔name cross-check)
- **`bagel_telemetry_check.py`** — mode-aware governance budget (quick ≤25%, full ≤40%) with token_log-derived share

```bash
python bagel-genesis/scripts/bagel_v3_check.py /path/to/project
python bagel-genesis/scripts/skill_lint.py bagel-genesis
```

## Enforcement honesty

BAGEL is unusually candid about what its validators can and cannot guarantee. Every validator is a Python checker the agent runs, reading `.bagel/` YAML the agent authored. The checkers verify **shape** (fields exist, enums valid, hashes match) — they raise the bar against lazy/careless cheating, but a determined adversarial agent that populates the full schema with fabricated data can still pass. Full closure requires **platform-level provenance** (externally-triggered gates, append-only signed state, real token accounting) — this is openly stated in the skill's Enforcement Honesty section.

## Changelog

### v5.0 — Mode-2 complete, execution-gap closure, externally-verified substrate

V5 completes the two halves of "an independent researcher who can do creative and innovative work," closes the gap between *designed protocol* and *actual agent behavior*, and puts the validator substrate itself under external CI:

- **Mode-2 split into two complete styles by `research_autonomy.objective`.** **Explorer** (`discovery`) returns vetted *novel ideas* under a **zero-blast-radius** sandbox contract (`research-explorer.md` + `discovery_sandbox_check.py`); **Optimizer** (`optimization`) chases the best *honest* benchmark score — may tune, swap, or replace the method — under an anti-gaming contract (`research-optimizer.md` + `optimization_integrity_check.py`: target+baseline locked first, every kept variant selected on validation not test, full variant denominator logged, headline bound to the Mode-1 confirmatory stack + attributed by ablation).
- **Mode-1 data-integrity + reproducibility floor** — `data_leakage_check.py` (all-data preprocessing / selecting-on-test / outcome-dependent exclusions) and `reproducibility_checklist_check.py` (NeurIPS/ICML checklist with every mechanical `yes` cross-checked against the real artifact, now robust to YAML boolean coercion).
- **Execution-gap closure** — `execution_fidelity_check.py` inverts skip-if-absent (a claim that implies an artifact fails when the artifact is absent); opt-in `BAGEL_REQUIRE_CONTROL_PLANE=1` blocks product writes at the tool boundary until the constitution exists, regardless of whether the agent read the protocol.
- **Producer-side templates** (`templates/`) so agents fill the schema instead of reconstructing it — each annotated with exactly what its gate checks, verified to pass end-to-end.
- **Externally-verified substrate** — `run_all_self_tests.py` runs every validator self-test in one command; the CI workflow gained a `validators` job running the consolidated self-tests + the 22-assertion mechanical grader on every push, so a gate cannot silently regress in a process the agent controls.

Structural limits kept honest: a gate proves the *protocol* was honest (locked target, val-selection, logged denominator, held-out confirmation), not that the test set never leaked into training — that audit composes with `data_leakage`; full ground-truth closure still needs the external CI/branch-protection the user configures.

### v4.3 — Research Lab Closure + Mode-2 Coverage Hardening

V4.3 closes the highest-impact findings from a 5-agent independent audit and upgrades research autonomy into a trustworthy, CI-verifiable autonomous-research substrate:

- **Mode-2 amendment dead path fixed** — the `{None, "", []}` set literal crashed `validate_amendment` on any well-formed amendment; now runs cleanly and enforces structured `expected_information_gain` / `confound_risk` / `protected_field_impact` + R3/R4 reviewer independence backed by `true_subagents.observed` proof (not self-attested strings).
- **Lab automation hardened** — pre-Build execution is no longer defeated by renaming `run_command` → `eval_script`/`setup`; the validator now recursively scans all lane string fields for executable command patterns and non-canonical LLM calls.
- **Platform attestation + CI auditor** — `PostToolUse`/`PreToolUse`/`Stop` Claude Code hooks sign every Bash/file/turn event with a key the agent cannot reach; a CI-side auditor binds headline claims to committed git bytes via command_ref pinning, asymmetric verdict signing, plan-before-runs DAG anchoring, per-seed run_ref uniqueness, and statistic recompute (catches fabricated p-values).
- **Environment lock** — `environment_lock_check.py` requires pip-freeze/cuda/determinism capture for Build-started research, closing the reproducibility gap.
- **Coverage governance** — `evals/coverage_map.py` (upgraded to a per-case guard) verifies every mechanical grader fixture builds and targets an existing validator, preventing the "validator exists but no fixture ever exercises it" failure class that hid the v4.2 crash.

Structural limits kept honest in docs: pinned-but-malicious protocol scripts still require human code review; full ground-truth closure needs external CI/branch-protection the user must configure (skill detects and degrades to UNATTESTED rather than over-claiming).

### v4.1 — Research Integrity Hardening

V4.1 closes the highest-risk research gaps: dataset-integrity now fires on the V4 research claim path, strict-mode authority refs must resolve to real human decisions, experiment plans are hash-bound, headline metrics can require recompute extractors, and stale long-run heartbeats fail the suite.

### v4.0 — Research Governance Layer

V4 adds explicit `protocol_execution` and `autonomous_researcher` modes for rigorous autonomous research, with preregistered experiment plans, experiment event logs, claim-evidence matrices, and mechanical checks against strict-protocol drift and post-hoc headline claims.

### v3.9 — External 9-agent audit (critical safety + integrity defects fixed)

A 9-agent, 3-round independent external review found critical defects all prior internal judges missed. Each claim was independently verified before fixing — 10/10 confirmed. Key fixes:

- **Emergency stop circuit breaker** — was a gate *failure* the agent was pressured to "repair" away; now HALTs unconditionally
- **`--replay` wired by default** — evidence was fully fabricable (zero commands run); now cited commands are re-executed
- **`.bagel/` privacy protection** — was silently committed to the user's git history; now gitignored before any commit
- **Outbound/exfiltration hard-stop** — the kill list was blind to send-email/publish/external-API/deploy; now included
- **Green-floor provenance** — a fabricated floor inverted the regression gate; now requires traced-to-delta provenance
- **Atomic writes + YAMLError guard** — half-written state crashed validators; now temp+replace + caught

### v3.7–v3.8 — Five-judge full-skill audit (73.2→83.8)

5 independent agents from different perspectives found 8 consensus weaknesses. All addressed: omission-as-pass closed, statistical-rigor + claim-evidence validators, output-side secret gate, NFR quality gates (a11y/performance), expert packs expanded, Security Engineer role, loading-matrix tiers, build-unlock checklist.

### v3.4–v3.6 — Semantic Integrity Runtime + deep gap closure

Mechanical anti-cheat validators: structured-declaration requirement axes (paraphrase-proof), token_log-derived governance share, credential scanner, court-verdict-accepted check, stale-skill-state detector.

### v3.1–v3.3 — Expert autonomy runtime + fault-path hardening

Executable expert runtime, measured autonomous loop, supervisor resilience, context-tree replacement policy.

## Honest boundaries

BAGEL improves the odds of high-quality autonomous work; it does not make model limits disappear.

- It excels at **true unattended overnight continuity** on large, cooperative, well-scoped builds.
- Control-plane tax is real (~25-40% governance overhead); it amortizes on genuinely long work.
- The enforcement substrate is **voluntary** (the agent runs its own auditor) — full closure needs platform hooks.
- It has not been A/B tested end-to-end vs direct prompting on a real messy codebase (this is the next step).

## License

MIT
