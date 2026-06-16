<div align="center">

# 🥯 BAGEL Genesis

**Turn a vague vision into a finished, high-quality deliverable — while you sleep.**

A skill-level operating protocol that makes an autonomous agent do *real expert work*, not just code generation: deep upfront alignment, multi-agent orchestration, calibrated long-running iteration, and hard-to-fake semantic integrity gates.

`Claude Code` · `Codex` · `Cursor` · any skills-compatible runtime

[![Skills Standard](https://img.shields.io/badge/Agent%20Skills-Standard-blue)](https://skills.sh)
[![Version](https://img.shields.io/badge/version-v3.7-green)](#changelog)
[![Evals](https://img.shields.io/badge/evals-120-orange)](evals/evals.json)
[![Darwin](https://img.shields.io/badge/Darwin-5%20judges-blueviolet)](#changelog)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

</div>

---

## Why BAGEL?

Most agent skills stop at "generate code." BAGEL is different — it encodes the **full expert workflow** that a principal engineer or researcher does before and during a multi-day build:

- **Clarify** a fuzzy goal into executable decisions before writing a line of code
- **Orchestrate** multiple specialized sub-agents (not one model doing everything)
- **Run autonomously** for hours through implementation, verification, recovery, and polish
- **Prove progress** with measurable deltas — not "it looks done"
- **Wake you** only for genuine hard-stops, not routine questions

And as of **V3.4**, it does all this as a **hard-to-fake runtime**: the expert council verdicts, risk assessments, dependency integrations, and research integrity claims are all *mechanically validated*, so an agent cannot satisfy the gates with empty placeholders or proxy substitutions.

---

## The 30-Second Pitch

```text
You:   "通宵帮我重构这个 SaaS 的认证和支付模块，从 session 迁移到 OAuth2 + Stripe。
        你看着办，明早看结果。"

BAGEL: → Aligns: captures Stop Contract (budget, hard-stops, morning briefing)
       → Detects: auth+payment+production_data = sensitive surfaces → risk_level=critical
       → Requires: Risk Officer + Systems Architect on the Expert Strategy Council
       → Orchestrates: Supervisor binds loop, spawns Orchestrator, dispatches workers
       → Validates: every council verdict has real content, every dependency uses real protocol
       → Morning: delivers working migration + evidence + briefing
```

---

## Core Architecture

```text
                    ┌─────────────────────────────────────────┐
                    │              USER (delegates)            │
                    └──────────────────┬──────────────────────┘
                                       │ vague vision + autonomy
                    ┌──────────────────▼──────────────────────┐
                    │            🔴 STOP CONTRACT              │
                    │  budget · hard-stops · morning return   │
                    └──────────────────┬──────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────┐
          ┌─────────┤            ALIGN PHASE                  ├─────────┐
          │         │  requirement coherence · problem frame  │         │
          │         │  leverage map · domain excellence       │         │
          │         └──────────────────┬──────────────────────┘         │
          │                            │ 🔴 BUILD UNLOCK                 │
          │         ┌──────────────────▼──────────────────────┐         │
          │         │           BUILD / ITERATE               │         │
   Supervisor ──────┤  slice → verify → evidence → review      ├──── Expert
   (heartbeat,       │  ↑                                    │     Council
    hard-stop        │  └── recovery on failure (shrink/      │  (Domain Expert,
    arbitration)     │      isolate/diagnose/switch)          │   Systems Arch,
                    └──────────────────┬──────────────────────┘   Evaluation
                                       │                            Skeptic,
                    ┌──────────────────▼──────────────────────┐    User Proxy,
                    │           🔴 FINAL DELIVERY              │    Risk Officer,
                    │  excellence horizon · bar raised         │    Innovation)
                    └─────────────────────────────────────────┘
```

**Four hard checkpoints** (marked 🔴) are the *only* places BAGEL pauses for you. Everything else is autonomy-solvable.

---

## What Makes It Hard-to-Fake (V3.4)

V3.4 added **Semantic Integrity validators** that catch the most common "form-satisfiable" shortcuts:

| Anti-cheat | What it catches | How |
|---|---|---|
| **Council output validation** | Empty/placeholder expert verdicts | Parses verdict YAML content — checks perspective match, verdict enum, ≥30-char reasoning, evidence-per-verdict-type |
| **Decision owner verification** | Fake Principal Expert identity | Cross-references `decision_owner` against dispatch registry records |
| **Derived risk enforcement** | Under-rating sensitive work | If `risk_basis.affected_surfaces` touches auth/payment/etc → `risk_level` must be high/critical (not self-report) |
| **Requirement coherence** | Mutually-exclusive requirements | Checks against contradiction families (CAP, latency-bandwidth, strong-vs-eventual-merge) before Build |
| **Premise fidelity** | Proxy substitution of user's claim | `proxy_used=true` without `user_authority_ref` fails; unfalsifiable premises can't become proxy experiments |
| **Named dependency protocol** | In-memory fallback for real deps | Scans product/test code for `in_memory`/`fake_redis`/`hashmap fallback` labels; `test_uses_real_endpoint` must be true |
| **Dataset integrity** | Test-set leakage | Requires split hashes + disjointness proof; `tuning_used_test_set=true` invalidates headline claims |
| **Schema drift prevention** | Validator reading undeclared fields | `skill_lint.py` auto-diffs agent schema docs vs validator field sets on every edit |

---

## Quick Start

### Install

```bash
git clone https://github.com/BRSAMAyu/bagel-genesis.git
# Copy or symlink into your agent's skills directory:
ln -s "$(pwd)/bagel-genesis" ~/.codex/skills/bagel-genesis      # Codex
ln -s "$(pwd)/bagel-genesis" ~/.claude/skills/bagel-genesis     # Claude Code
```

### Use

Just describe your goal and delegate:

```text
Use bagel-genesis.

I have a rough idea for a [product/research/tool]. Here's what I want:
...

Start with deep alignment, then run stable_long_run autonomous iteration.
Wake me only for true hard-stops. I want a morning briefing.
```

Or for an existing project:

```text
Use bagel-genesis.

This repo is an existing project. Run Project Cartographer first to understand
what exists and what must be preserved. Then run autonomous polish and optimization.
```

### Validate

```bash
# Validate the skill itself (schema drift, cross-file consistency)
python bagel-genesis/scripts/skill_lint.py bagel-genesis

# Validate a running BAGEL project (all 17+ runtime checks)
python bagel-genesis/scripts/bagel_v3_check.py /path/to/project

# Dryrun the test-prompts regression suite
python bagel-genesis/scripts/test_prompts_dryrun.py bagel-genesis
```

---

## The Three Phases

### Align → Build → Polish

| Phase | What happens | Gate |
|---|---|---|
| **Align** | Capture vision, taste, hard-stops. Reframe the stated problem. Map leverage. Calibrate what "excellent" means for this domain. | 🔴 STOP CONTRACT captured |
| **Build** | Slice into bounded chunks. Each slice: implement → verify → record evidence → review. Recover on failure. | 🔴 BUILD UNLOCK (all gates pass) |
| **Polish** | Critique, raise the bar, verify. Continue until budget exhausted or excellence horizon reached. | 🔴 FINAL DELIVERY |

**The tie-breaker:** when friction hits, BAGEL continues by default — repair, shrink, isolate, switch strategy, or work on another high-value task. It wakes you only for genuine hard-stops (irreversible damage, credentials, production data, core identity changes).

---

## Expert Strategy Council

For high-impact decisions, BAGEL convenes a real multi-agent council — each member is a dispatched sub-agent with a verified dispatch record, not a role-play:

| Role | When required | Focus |
|---|---|---|
| **Domain Expert** | always | What "excellent" means here; observable signals |
| **Evaluation Skeptic** | always | Is the metric gameable? Can it distinguish good from excellent? |
| **User Proxy** | always | Does this serve the user's actual intent? |
| **Systems Architect** | architecture/route decisions | Structural soundness, blast radius |
| **Risk Officer** | high/critical risk | Sensitive surfaces, reversibility, authority |
| **Innovation Strategist** | breakthrough probes | Non-local improvements |

The **Principal Expert** synthesizes council verdicts + evidence + ROI into one binding `expert_decision_v1` record — with mechanically-validated risk derivation and owner identity.

---

## Six Domain Expert Packs

Each pack provides executable methodology (not just rubrics) for its artifact type:

| Pack | Coverage |
|---|---|
| `software-product` | ghost-ship gate, typed contracts, slice-based delivery |
| `research-experiment` | falsifiable hypothesis, ≥3 seeds, ablation matrix, FLOP accounting at iso-compute, statistical rigor, dataset integrity, practical significance |
| `writing-longform` | premise pressure test, desire-conflict matrix, scene turns, anti-exposition, voice lock, continuity ledger |
| `design-ui` | visual hierarchy, interaction completeness, accessibility |
| `data-analysis` | hypothesis-driven analysis, statistical validity, honest visualization |
| `ops-sre` | event-driven mode (observe/autofix/guarded), blast radius, rollback plans |

---

## Repository Layout

```text
bagel-genesis/
├── SKILL.md                    # Entry point — the operating protocol
├── agents/                     # 26 role prompts (Orchestrator, workers, council, experts)
├── references/                 # 63 trigger-loaded protocols
│   ├── expert-packs/           # 6 domain-specific methodology packs
│   ├── gate-predicates.md      # 41 hard gates (mechanically + agent-attested tiers)
│   └── ...
├── scripts/                    # 23 validation & runtime scripts
│   ├── bagel_v3_check.py       # Master validator (17+ sub-checks)
│   ├── expert_strategy_check.py# Expert autonomy + semantic integrity
│   ├── skill_lint.py           # Schema-drift + cross-file consistency
│   ├── test_prompts_dryrun.py  # Test-prompts regression suite
│   └── ...
├── evals/
│   └── evals.json              # 120 behavior evals
└── test-prompts.json           # 4 hard-scenario pressure tests
```

---

## Safety Model

BAGEL is **autonomy-first, not reckless**.

**Continues through** (autonomy-solvable):
- missing tests, verifiers, or local tools → Runtime Doctor provisions them
- broken environment → docker-compose/mock-server repair (real protocol, not in-process stub)
- failing experiments → strategy switch / breakthrough search
- review failures, blocked lanes, UI gaps

**Wakes you only for** (hard-stop boundaries):
- irreversible or non-recoverable destructive action
- production data or infrastructure changes
- credentials, tokens, paid resources
- serious security/privacy/legal/financial risk
- core product or research identity changes
- explicit user-forbidden boundaries

---

## Runtime Validation (17+ checks)

`bagel_v3_check.py` orchestrates a comprehensive validation suite against any running BAGEL project:

```text
✓ bagel_run_check         ✓ supervisor_boundary      ✓ runtime_proof
✓ dispatch_envelope       ✓ flywheel                 ✓ bagel_memory
✓ bagel_telemetry         ✓ deliverable_delta        ✓ resume_integrity
✓ evidence_replay         ✓ scope                    ✓ evaluation_quality
✓ expert_strategy         ✓ roi                      ✓ alignment_freshness
✓ reference_load          ✓ emergency_stop
```

Each check exits non-zero on failure, making the gate mechanically enforced.

---

## <a id="changelog"></a>Changelog

### v3.7 — Five-judge full-skill audit (5 independent perspectives, 6 consensus weaknesses fixed)

Dispatched 5 independent agents from completely different perspectives (architecture/coherence, adversarial red-team, usability/executability, research-integrity, completeness/coverage) to freely and fully review the entire skill. They found 8 consensus weaknesses (C1-C8) the prior same-context judges had missed. 5 Darwin rounds fixed C1-C6:

- **C1 (omission-as-pass):** scope_check + dispatch now derive coverage from `git diff` — an agent that makes out-of-scope edits without recording a scope_delta **fails** (was: silently passed when the record was omitted)
- **C2 (statistical rigor):** new `validate_statistical_rigor` — headline claims require n_seeds≥5, a significance test (paired_t/wilcoxon/bootstrap) with p_value, effect_size, correction, AND **p_value < pre_registered_threshold** (presence-only was theater)
- **C3 (claim-evidence matrix):** new `validate_claim_evidence_matrix` — each claim maps to metric + run_refs (files must exist) + ablation_status + reproducibility_status; headline claims fail if ablation=pending or repro=missing
- **C4 (output-side secret leak):** new `no_hardcoded_secrets` gate — scans generated code for AWS keys / GitHub PATs / private key blocks / Stripe live keys / Slack tokens; fails **unconditionally** (no acknowledgment can clear a committed secret)
- **C5 (gate-index drift):** SKILL.md Hard Gates replaced static 40-item list with family-grouped pointer to the authoritative 53-predicate table + `skill_lint.check_version_drift` catches future drift
- **C6 (v2_check + compact):** orchestrator.md v2_check→v3_check, "Context Compaction" → "Context Hygiene (handoff-and-replace)" — aligns with replace-not-compact policy

Remaining (C7 a11y/perf/i18n ungated, C8 evidence existence-only for non-dataset claims) are disclosed as known limits — they require domain-specific tooling integration (axe-core, Lighthouse) beyond skill-scope validators.

### v3.6 — Deep gap closure (Darwin ratchet, 88.6→91.1)

Closed the 3 gaps that v3.5 had conservatively declared "implementation-engineering boundaries (HL-4)." Independent judges (K–R) proved each was closeable at the skill-design level through structured-declaration, recomputable derivation, and fixed-shape pattern scanning:

- **Gap1 (paraphrase-evasion):** S2 `requirement_coherence` and S4 `gameable_metric_pairing` now use a **mandatory structured-declaration** path (existence-gated, not signal-gated) — the agent must declare `requirement_axes` from a fixed enum or explicitly attest `no_contradiction_axes_needed` (cross-validated against the stated-problem text); `metric_role` is mandatory on every metric with a role↔name cross-check. A synonym can no longer route around the structured path.
- **Gap2 (self-reported budget):** `governance_token_share` is now **derived from `token_log`** (mandatory for deliverable-producing cycles) — the validator recomputes governance-category tokens / all tokens and fails if the declared share deviates >5% from the derived value. A self-reported lie is now caught.
- **Gap3 (no production-data scanner):** new `scripts/production_surface_check.py` scans source/config/dispatch for cloud keys (AKIA shapes), non-localhost production connection strings, prod-host patterns, and cloud-SDK usage; detected signals require a **structured** hard-stop acknowledgment (`hardstop_type: production_data` + `acknowledged: true`), not a free-text keyword.

Residual limits (honestly disclosed as platform boundaries): keyword fallbacks evadable by renaming variables (structured paths are the paraphrase-proof alternative); token_log entries agent-recorded (platform provenance would be stronger); env-var/ORM-config indirection not caught by the credential scanner (human STOP is the final authority).

### v3.5 — High-pressure scenario validation (Darwin 4-round ratchet, 83.8→88.6)

Validated the skill against **9 adversarial pressure scenarios** (fault-injection recovery, CAP contradictions, unfalsifiable premises, gameable metrics, monorepo takeover, compaction/resume, production-data hard-stop, governance-budget overload, mid-run scope creep) using independent blind judges. Each round kept only improvements; the ratchet exposed progressively deeper layers until convergence at an implementation-engineering boundary (HL-4).

**Mechanical gates promoted from agent-attested to enforced:**
- `requirement_coherence_checked` — CAP/latency/strong-vs-eventual/realtime/cost contradiction families; a matched family requires a human decision that *names the family AND carries a resolution action* (a generic "tradeoff" note no longer clears it)
- `premise_falsifiable` — unfalsifiable subjects (consciousness/qualia/free-will) + prove/exists claims route to 🔴 S1 hard-stop, not silent execution
- `gameable_metric_paired` — a retrieval headline (hit@1/precision@1/exact-match) cannot be the sole quality signal without a robustness pair (MRR/nDCG/recall@k/held-out)
- `court_verdict_accepted` — a Constitutional Court ref must point at a record whose verdict is accepted; a rejected/stub ruling fails scope_delta
- `stale_skill_state` — diffs the SKILL.md hash recorded at spawn against the current skill; a stale topology must be re-anchored, not obeyed
- Mode-aware governance budget — quick ≤25%, full ≤40%, per-cycle hard fail (was a flat 30% with streak-warning-only)

**Honesty layer:** the Enforcement Model now stratifies gates into robust-mechanical / lexical-keyword / mixed / agent-attested-by-design, and an "Enforcement honesty" section in SKILL.md discloses the 3 known limits (keyword matchers evadable by paraphrase; governance_token_share self-reported; production-data STOP is a human checkpoint by design) — all implementation/platform boundaries, not skill-design gaps.

### v3.4.1 — Darwin convergence (Semantic Integrity Runtime)
- Fixed `path_ref` runtime bug found by Darwin independent judge (P0-1 council validation was unreachable)
- Closed named-dependency opt-out hole (missing record now inferred from evidence)
- Added V3.4 Semantic Integrity Checks table to SKILL.md

### v3.4 — Semantic Integrity Runtime (hard-to-fake expert runtime)
- **P0-1** Council output content validation (verdict body, not just file existence)
- **P0-2** Decision owner dispatch registry verification
- **P0-3** `risk_level`/`risk_basis`/`authority_ref` schema + derived risk checks
- **P0-4** Supervisor boundary schema enforcement + expanded forbidden commands
- **P0-5** Parent/child dispatch path conflict detection
- **P0-6** `git_target` split (branch names with `/` no longer false-flagged)
- **P0-7** Domain freshness hard-enforce by expert layer mode
- **P0-8** Premise fidelity / proxy substitution defense
- **P0-9** Named dependency protocol substitution check
- **P0-10** Dataset integrity (split hashes, disjointness, test-set tuning)
- **P1** Schema drift lint, test-prompts dryrun CI, reference source_hash grouping, governance budget breakdown, writing-longform + ops-sre pack expansion

### v3.3 — Coding + research fault-path hardening
- Requirement Coherence Check + contradiction-family table
- Unfalsifiable-premise termination rule
- Runtime Doctor repair primitives (docker-compose/mock-server, forbid in-process stub)
- Gates promoted from prose to agent-attested mechanism

### v3.2 — Darwin-optimized skill quality (71→85.9)
- Visual 🔴 checkpoint markers + autonomy-vs-checkpoint disambiguation
- Consolidated Anti-Patterns & Red Lights chapter (14 entries)
- Softened hedges → precise thresholds (25%/40% governance budget)
- Research-experiment pack: 8-step experimental methodology + statistical rigor

### v3.1 — Executable Expert Runtime
- Expert Strategy Council with real dispatch, Expert Decision v1 schema, ROI controller

### v3.0 — Expert Autonomy Layer
### v2.0 — Measured Runtime (evidence-not-trust, replace-not-compact)
### v1.0 — Initial protocol

---

## Credits & Inspiration

- **[Karpathy autoresearch](https://github.com/karpathy/autoresearch)** — the "only keep measurable improvements" ratchet philosophy that inspired the Darwin optimization process used to refine this skill (v3.2→v3.4 were each validated by independent judge agents, keeping only changes that measurably improved quality).
- **[Microsoft SkillLens](https://arxiv.org/abs/2605.23899)** — empirical evidence that LLM-as-judge skill evaluation is only 46.4% accurate; adding meta-skill dimensions (anti-patterns, failure modes) raises it to 73.8%. BAGEL's 9-dimension rubric and anti-cheat validators are grounded in this research.

---

## License

MIT
