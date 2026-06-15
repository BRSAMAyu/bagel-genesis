# Deep Alignment Protocol

Use before autonomous execution. The goal is to make the user's implicit vision explicit enough that the system can run for many hours without constant intervention.

## Alignment Outputs

Create:

- `.bagel/alignment/vision-canon.md`
- `.bagel/alignment/decision-map.yaml`
- `.bagel/alignment/autonomy-contract.yaml`
- `.bagel/alignment/assumption-ledger.yaml`
- `.bagel/alignment/challenge-log.md`
- `.bagel/excellence_horizon.yaml`

For existing projects, also require `.bagel/agent_context/project-facts.yaml` and related project-understanding files before finalizing alignment. The vision must be aligned with the real current project, not just the user's description.

Keep these concise and operational. They are control artifacts, not essays.

## Interaction Mechanics

Use the platform's best user-input surface for alignment. When Codex or Claude Code exposes structured choice prompts, use them for decisions with a known option set; otherwise write compact numbered choices in chat. Ask at most three questions at once. Prefer one high-leverage question over a survey.

Do not switch into a planning-only mode that waits for the user after the user has said "start autonomous iteration", "run overnight", "keep improving", or equivalent. Alignment is a decision-capture phase, not a place to park the task. Once the required choices below are captured or safely defaulted, start the runtime loop.

Before asking choices, briefly introduce BAGEL in plain language:

```text
BAGEL will first align on vision, safety boundaries, runtime strategy, and what "excellent" means. Then it will run autonomous cycles: build or research, verify, record progress, improve, and continue until the agreed budget, completion/excellence horizon, user stop, or a true hard-stop.
```

Question types:

- **Choice question:** use when the answer changes runtime policy, safety boundaries, budget allocation, takeover scope, taste direction, or review strictness. Provide 2-4 neutral options, put the recommended option first, and include one sentence about the tradeoff.
- **Open question:** use when the user's mental model is likely richer than any option list. Include a short "why this matters" note, 2-3 neutral examples, and a safe default if the user skips it.
- **Veto question:** for existing projects, let the system draft facts from repo evidence, then ask the user to veto or correct protected behaviors, accidental conventions, and product promises.

Never make the user do work the repo or artifact can answer. Use project discovery for project facts; use the user for intent, fear, taste, hard boundaries, and success judgment.

Persist every answered or defaulted alignment decision immediately:

```yaml
alignment_decision:
  id: "AD-001"
  prompt: "How autonomous should this run be?"
  answer_type: choice | open | veto | inferred_default
  selected: "max_autonomy_inside_hard_stops"
  rationale: "User wants overnight execution without routine approval."
  tradeoff_acknowledged: "Higher autonomy, bounded by hard-stop list."
  source: user_explicit | user_veto | system_inferred | project_evidence
  confidence: high | medium | low
  revisitable: true
  stored_in:
    - ".bagel/constitution.yaml#autonomy_contract"
```

If the user is unsure, do not force premature precision. Record the uncertainty, choose a reversible default, and add a "morning review" item in `.bagel/STATUS.md`.

## Run-Mode Depth

Use the lightest alignment depth that makes unattended work executable. Each tier has a **mechanical floor** - the run must not enter Build until the floor is met and recorded as `alignment_decision` entries in the constitution.

- `snap_alignment`: urgent or low-stakes. **Floor: >= 4 questions (the fast-path set), <= 1 round.** Ask only the essential choices, default the rest, then start. Usually 3-7 minutes.
- `standard_alignment`: default. **Floor: all 8 choice cards asked + >= 3 open questions, >= 1 round.** Ask the choice cards plus the most relevant open questions. Usually 10-25 minutes.
- `deep_alignment`: important, ambiguous, high-budget, or large-scope. **Floor: >= 2 rounds, >= 8 total questions, all 8 choice cards + >= 5 open questions.** After each round, explicitly ask the user "Is your mental model clear enough to delegate this overnight?" - only an explicit yes ends alignment. Multiple rounds are the norm, not the exception.

**Alignment Floor Checklist (mechanical):** the constitution must contain >= 8 `alignment_decision` records (standard) or >= 12 (deep) before it is considered locked. If the count is below the floor for the selected depth, the `constitution_approved` gate fails and Build must not start. This is what stops alignment from collapsing to native-plan-mode depth.

The "ask at most three questions at once" rule (above) caps **batch size**, not total depth. In standard and deep modes, ask multiple batches across one or more rounds until the floor is met.

Do not spend the first hours of a run producing governance documents when a bounded, reversible implementation or experiment can already produce evidence - but do not use this as an excuse to skip the depth floor. The floor is a minimum, not a maximum.

## Alignment Question Tree

Ask enough of these to make the next autonomous run safe and useful. Do not ask them mechanically; skip answers already supplied.

### Fast path (the 4 questions that carry ~80% of the value)

**The fast path is ONLY valid when the selected depth is `snap_alignment`.** In `standard_alignment` or `deep_alignment`, using the fast path as the whole alignment is a violation - it does not meet the depth floor and the `constitution_approved` gate will fail.

If the user is tired, time-constrained, or just wants to delegate fast AND has explicitly chosen `snap_alignment`, get crisp answers to these four and start. The rest can be inferred, defaulted, or asked only if a hard-stop ambiguity remains:

1. **Core vision** (Q1): What are we making, for whom, what pain does it solve?
2. **Disappointment** (Q3): What outcome would disappoint you even if it technically works? — this is the strongest single alignment signal.
3. **Hard-stops** (Q7): Which choices are true hard-stops I must wake you for (irreversible, paid, credentialed, production, legal/privacy, core identity)?
4. **Budget + return** (Q13 + Q14): How long may I run, and what do you want to see in STATUS.md when you wake?

Taste/exemplars (Q8/Q10) are high-value if the user has them ready, but if not, default to the constitution's taste kernel and surface style options in the morning briefing instead of guessing all night.

### Choice Cards

Use these as default option sets. Adapt labels to the artifact, but preserve the tradeoffs.

#### Alignment Depth

```yaml
question: "How deep should the pre-run alignment be?"
options:
  - label: "Standard alignment"
    description: "Recommended default: enough choices to run safely without turning alignment into the work."
  - label: "Snap alignment"
    description: "For urgency: capture essentials, let BAGEL infer reversible details, and start quickly."
  - label: "Deep alignment"
    description: "For important or high-budget work: continue asking decision points until the user is satisfied."
```

#### Execution Strategy

```yaml
question: "Which execution strategy should BAGEL use?"
options:
  - label: "Stable long-run"
    description: "Best for overnight work: low write parallelism, stronger verification, continuous autonomous cycles."
  - label: "Balanced parallel"
    description: "Moderate concurrency and review depth; good when speed and reliability both matter."
  - label: "Fast parallel"
    description: "Maximum exploration speed; more suitable when the user is nearby and rollback is cheap."
```

Persist as:

```yaml
run_strategy:
  execution_strategy: stable_long_run | balanced_parallel | fast_parallel
  alignment_depth: snap_alignment | standard_alignment | deep_alignment
  plan_mode_policy: avoid_after_alignment
```

#### Autonomy Level

```yaml
question: "How much autonomy should BAGEL use after this alignment?"
options:
  - label: "Maximum inside hard-stops"
    description: "Best for overnight work: the system decides all reversible details and wakes only for hard-stops."
  - label: "Conservative autonomous"
    description: "The system continues independently, but avoids broad redesigns and dependency/toolchain changes."
  - label: "Checkpoints after milestones"
    description: "The system works autonomously within each milestone, then pauses for review before the next milestone."
```

#### Run Budget

```yaml
question: "What should the run spend before returning a final or checkpointed result?"
options:
  - label: "Use the available night"
    description: "Keep iterating until the time/token budget is exhausted or the excellence horizon passes."
  - label: "Baseline first"
    description: "Prioritize a complete usable baseline, then spend remaining budget on polish."
  - label: "Strict cap"
    description: "Stop at a specified time/token ceiling even if high-value work remains."
```

When autonomous iteration is enabled, also capture hard numeric controls:

```yaml
iteration_controls:
  target_cycles: 12
  max_cycles: 24
  checkpoint_every_minutes: 30
  timer_interval_minutes: 10
  max_consecutive_lateral_cycles: 3
  max_consecutive_failures_same_gate: 3
```

If the user does not know the numbers, choose defaults from execution strategy:

- `stable_long_run`: timer 10-15 minutes, checkpoint 30 minutes, target 12 cycles, max 24.
- `balanced_parallel`: timer 10 minutes, checkpoint 20 minutes, target 8 cycles, max 16.
- `fast_parallel`: timer 5-10 minutes, checkpoint 15 minutes, target 6 cycles, max 12.

These are control targets, not excuses to stop while budget and high-value work remain.

### Stop Contract (MANDATORY before any autonomous work)

The Stop Contract is a single mandatory alignment artifact that captures *when the run ends*. It is the most important thing to agree on before the user goes to sleep, because once the loop is running, the agent's stop behavior is governed by these numbers, not by self-judgment.

**Ordering (resolved):** capability detection -> bind loop -> begin Align -> capture Stop Contract as the FIRST alignment artifact -> continue Align to depth floor -> enter Build. The loop is bound before Align (per loop-runtime Start Gate); the Stop Contract is captured as the first thing once Align begins. **Do not enter Build until the Stop Contract is captured and persisted to `.bagel/constitution.yaml` (quick) or `.bagel/constitution.json` (full).**

Ask these explicitly as choice cards or crisp numeric questions. Do not infer or default them silently - the user must consciously set them, because they define the overnight contract:

```yaml
stop_contract:
  # When does the run end? (any one of these triggers a stop)
  max_iterations: 24              # hard ceiling on iterations; default from execution strategy
  budget_limit: "available_night" # "available_night" | "strict_cap: <hours or tokens>" | "baseline_first"
  target_iterations: 12           # soft target; reaching it is NOT a stop - it means "raise the bar"

  # What stops the run immediately (hard-stops, non-negotiable)?
  hard_stops:
    - "irreversible or non-recoverable destructive action"
    - "credentials, tokens, paid accounts or paid services"
    - "production data or production infrastructure"
    - "serious security/privacy/legal/financial risk"
    - "core product/research identity changes"
    # + any user-specific hard-stops captured here

  # What does NOT stop the run? (autonomy scope)
  within_autonomy:
    - "missing tests/verifiers (agent builds them)"
    - "broken local setup (agent fixes it)"
    - "failing experiments (agent tries alternatives)"
    - "review failures (agent addresses findings)"
    - "tool/env failures (agent recovers or switches lanes)"

  # What does the user want to see when they wake?
  morning_return: "a working baseline + polish pass + honest STATUS with what's done/undone/blocked"

  # May the agent run all night, or is there a wall-clock deadline?
  deadline: "none"   # "none" | ISO-8601 timestamp | "wake_by_08:00_local"
```

**The Stop Contract is enforced mechanically:** `bagel_run_check.py` fails the run if `stop_contract` is missing from constitution after alignment. `flywheel_check.py` uses `max_iterations` as the iteration-budget gate. The loop wake prompt does not need to repeat these - they live in `.bagel/constitution.yaml`, which the agent reads on every wake via progressive disclosure.

#### Existing Project Takeover

```yaml
question: "How aggressively may BAGEL change the existing project?"
options:
  - label: "Improve within current identity"
    description: "Preserve product promise and architecture direction; freely improve reversible implementation and UX."
  - label: "Aggressive redesign"
    description: "Allow major local redesigns if evidence shows they improve the goal, while preserving hard-stops."
  - label: "Surgical module work"
    description: "Only touch the target module or feature unless tests prove an adjacent change is required."
```

#### Taste Source

```yaml
question: "What should guide taste and quality decisions?"
options:
  - label: "Use exemplars"
    description: "User provides references or screenshots; BAGEL compares outputs against them."
  - label: "Infer from domain"
    description: "BAGEL chooses a domain-appropriate taste kernel and records assumptions for review."
  - label: "Preserve current style"
    description: "Existing project style dominates unless it clearly conflicts with the goal."
```

#### Research Verification

```yaml
question: "What kind of evidence can prove progress?"
options:
  - label: "Computable benchmark"
    description: "Use metrics, tests, simulations, ablations, or repeated runs to keep winners."
  - label: "Argument and source review"
    description: "Use claim-evidence maps, methodology critique, and independent review."
  - label: "Exploratory hypothesis generation"
    description: "Generate and test plausible paths, while labeling claims that lack ground truth."
```

#### Hard-Stop Boundary

```yaml
question: "Which boundaries must wake you before action?"
options:
  - label: "Only true hard-stops"
    description: "Irreversible/destructive, credentials, paid services, production data/infra, legal/privacy/security, or core identity changes."
  - label: "Hard-stops plus broad redesign"
    description: "Also pause before major architecture or product-flow redesigns."
  - label: "Custom boundary"
    description: "User names extra forbidden actions; BAGEL records them explicitly."
```

### Open Question Guidance

For open questions, use this format:

```text
Question: ...
Why this matters: ...
Examples, not suggestions:
- ...
- ...
Safe default if you skip: ...
How I will store it: ...
```

Examples must be neutral and diverse. Do not lead the user toward the agent's preferred implementation. The goal is to help the user recognize their own preference, not to sell an option.

### For existing projects: questions 17-19 are answered by the cartographer, not the user

For a takeover, the user often cannot answer "which conventions are protected" or "what already works." Route 17-19 to the **Project Cartographer**: it inspects the repo, infers protected vs. replaceable conventions, and produces a draft the user only **vetoes or approves**. Do not block alignment waiting for the user to articulate repo facts they may not know. Ask the user only for items the cartographer cannot infer (intentional product promises, business constraints).

### Core Vision

1. What are we making, for whom, and what pain or desire does it solve?
2. If this succeeds, how would you describe it to a smart friend in one sentence?
3. What outcome would disappoint you even if the artifact technically works?

### Boundaries

4. What must not change?
5. What are you most afraid the agent will decide incorrectly while running unattended?
6. Which reversible choices should the system decide alone?
7. Which choices are true hard-stops: irreversible, paid, credentialed, production, legal/privacy/security, or core identity changes?

### Taste and Exemplars

8. Name 2-3 products, papers, essays, apps, or artifacts you want this to resemble, and why.
9. Name 2-3 anti-examples, and what to avoid.
10. Pick 3-5 words for the final artifact's quality signature.

### Success and Runtime

11. What must be true before this counts as baseline complete?
12. What would make the result feel unexpectedly excellent?
13. How long may the system run, and what token/runtime budget should it spend?
14. When you return, what do you want to see in `.bagel/STATUS.md`?

### Research and Experiment Tasks

15. What metric, benchmark, proof obligation, or observation would convince us an idea is better?
16. What domains are computationally verifiable now, and what claims would need real-world/physical evidence later?

### Existing Projects

17. Which modules, behaviors, conventions, and user promises are protected?
18. Which areas may be redesigned aggressively?
19. What already works and should not be rebuilt?

## Vision Canon

Capture:

- the core promise,
- target users/audience/readers/stakeholders,
- excluded audiences and non-goals,
- desired emotional/quality/taste signature,
- comparable works/products and anti-examples,
- constraints and resources,
- expected final deliverable format,
- what would disappoint the user even if technically complete.
- for existing projects, which current behaviors and conventions are intentional, accidental, replaceable, or protected.

In `quick_autonomy`, store the canon in `.bagel/constitution.yaml`:

```yaml
vision:
  north_star: ""
  target_users: []
  excluded_users: []
  core_promise: ""
  disappointment_tests: []
  must_preserve: []
  non_goals: []
  constraints:
    platform: []
    privacy: []
    budget: ""
    deadline: ""
    deployment: ""
taste_kernel:
  exemplars: []
  anti_examples: []
  quality_words: []
  inferred_defaults:
    - assumption: ""
      confidence: low | medium | high
      review_when: "morning_briefing | before_final | never"
completion_horizon:
  baseline_must_have: []
  accepted_deferred_items: []
excellence_horizon:
  astonishing_if: []
  visual_or_domain_evidence_required: []
autonomy_contract:
  level: max_inside_hard_stops | conservative_autonomous | milestone_checkpoints | custom
  execution_strategy: stable_long_run | balanced_parallel | fast_parallel
  alignment_depth: snap_alignment | standard_alignment | deep_alignment
  system_may_decide: []
  system_must_wake_user: []
  user_fears: []
  runtime_budget: ""
  iteration_controls:
    target_cycles: 12
    max_cycles: 24
    checkpoint_every_minutes: 30
    timer_interval_minutes: 10
    max_consecutive_lateral_cycles: 3
    max_consecutive_failures_same_gate: 3
briefing_preferences:
  markdown_status: true
  html_dashboard:
    enabled: true | false
    mode: continuous_dashboard | section_tabs | slide_like_walkthrough
    style: calm_operator | product_studio | research_lab
    update_frequency: every_milestone | every_cycle | final_only
```

## Decision Map

Classify every important decision:

```yaml
decision:
  id: "D-001"
  question: "What should the onboarding tone be?"
  class: logic | convention | taste | philosophy | irreversible
  owner: system | user | court
  autonomy: decide | decide_and_log | propose_then_ask | must_ask
  evidence_needed: [examples, user_preference, domain_research]
  default_policy: "choose the option that best preserves the core promise"
```

Default to system decision for reversible logic, convention, local taste decisions, high-value UX polish, local tooling, test strategy, experiment design, and non-destructive implementation choices. Ask the user only when the decision changes the core promise, privacy/legal/financial/safety posture, target audience, production data/infrastructure, credentials/paid resources, or an irreversible direction.

Use decision cards for unresolved choices:

```yaml
decision_card:
  id: "D-004"
  decision: "How should onboarding behave?"
  why_it_matters: "This affects first-run UX and what the agent may redesign overnight."
  options:
    - id: "A"
      label: "Guided setup"
      tradeoff: "More helpful, more UI surface."
    - id: "B"
      label: "Fast direct entry"
      tradeoff: "Less friction, less explanation."
  recommended: "A"
  recommendation_reason: "Matches the stated target user."
  default_if_unanswered: "A, because reversible and locally changeable."
  owner: system | user | court
  wake_required_if_changed_later: true | false
```

When using platform choice UI, ask the `options` as the interactive choices and persist the selected `id`. For open decisions, keep `options: []` and store the user's answer verbatim plus the system's operational interpretation.

## Challenge Protocol

The system must challenge user instructions when they appear harmful to the stated goal.

Challenge when:

- instruction conflicts with the constitution,
- user asks for a shortcut that lowers quality,
- requested direction is likely to fail in the target domain,
- user assumption contradicts evidence from the project,
- instruction creates privacy, safety, legal, data-loss, or cost risk,
- requested change would consume large budget with weak expected value.

Challenge format:

```text
Concern: ...
Why it matters: ...
Options:
- A: ...
- B: ...
Recommendation: ...
Decision needed: yes/no
```

After consensus, update the decision map and constitution if needed.

## Autonomy Contract

Create `.bagel/alignment/autonomy-contract.yaml`:

```yaml
autonomy_contract:
  mode: supervised_start_then_max_autonomy
  system_may_decide:
    - implementation details
    - local UX copy
    - high-value UX and UI polish
    - non-core feature enhancements with positive expected value
    - reversible architecture choices
    - test strategy
    - local verifier and benchmark creation
    - project-local environment and tooling repairs
    - experiment hypotheses, metrics, and iteration plans
    - alternative implementation or research paths after failure
    - minor scope sequencing
    - bug and environment repairs
    - rollback and retry for agent-owned changes
  system_must_challenge_user:
    - quality-lowering shortcuts
    - contradictory requirements
    - high-cost low-value work
  system_must_wake_user:
    - irreversible or non-recoverable destructive action
    - serious security/privacy/legal/financial/production-data risk
    - paid external services or credentials
    - production infrastructure or production data changes
    - privacy/business-model/core-audience/core-promise changes
    - explicit user-forbidden boundary
  unattended_policy:
    continue_after_quota_resumes: true
    prefer_repair_over_blocking: true
    prefer_alternative_work_over_waiting: true
    self_provision_missing_local_tools: true
    generate_high_ev_improvements: true
    max_excellence_iterations: 3       # how many target-set->all-green cycles; each raises the bar. User-set; default 3.
    write_resume_checkpoint_every_cycle: true
```

Use the strongest autonomy contract the user will allow. The point of the alignment phase is to make later confirmation unnecessary for reversible, local, beneficial work.

## Excellence Horizon

Define what "excellent enough to stop" means. **Independent review is the primary assessment axis; quantitative metrics are an optional objective anchor.** During alignment, ask the user whether they can name concrete measurable targets for this artifact — if yes, capture them below; if not (common for writing, taste-driven UI, exploratory research), rely on independent review and mark the run's assessments as `low_confidence` (see excellence-loop Progress Delta Gate).

```yaml
excellence_horizon:
  baseline:
    - core workflows complete
    - verification passes
  # OPTIONAL but high-value: concrete measurable targets the run can check every cycle.
  # When defined, these become the Track-2 objective anchor for forward/lateral/backward.
  # Leave empty [] for artifacts that resist quantification; the run then relies on
  # independent review (Track 1) and marks deltas low_confidence.
  quantitative: []
    # examples (use only what applies; delete the rest):
    # - metric: test_coverage
    #   target: ">= 80%"
    #   command: "npm run test:coverage"
    #   direction: higher_is_better
    # - metric: lighthouse_performance
    #   target: ">= 90"
    #   command: "npx lighthouse --only-categories=performance --output=json http://localhost:3000"
    #   direction: higher_is_better
    # - metric: e2e_pass_rate
    #   target: "100%"
    #   command: "npx playwright test"
    #   direction: higher_is_better
    # - metric: benchmark_score
    #   target: "> baseline_2026-06-15"
    #   command: "python benchmarks/run.py --baseline"
    #   direction: higher_is_better
    # - metric: a11y_violations
    #   target: "0"
    #   command: "npx axe-core http://localhost:3000"
    #   direction: lower_is_better
    # - metric: bundle_size_kb
    #   target: "< 200"
    #   command: "npm run build && du -sh dist/"
    #   direction: lower_is_better
  high_finish:
    - no obvious UX/content/research/engineering gaps
    - reviewers at the QA-required independence level find no P0/P1/P2 with positive expected value
    - setup and reproduction are verified
    - documentation/user briefing is clear at multiple depths
    - if quantitative targets were defined, all are met
  diminishing_returns:
    min_review_rounds_without_high_value_findings: 2
    max_low_value_polish_rounds: 1
  stop_policy:
    continue_until: excellence_horizon_passed | budget_exhausted | user_stop | hard_stop_boundary
    no_idle_waiting: true
```

The excellence horizon defines the **starting** quality bar, not the stopping point. Meeting all targets is not done — it is the signal to raise the bar (see `excellence-loop.md` Bar-Raising Protocol). If the user provides quantitative targets, they are binding minimums: the run must not declare done while one is unmet, a metric regression is always `backward`, and once all are met the agent generates higher targets or new quality dimensions and keeps iterating. Stopping happens only under the stringent conditions in `excellence-loop.md` Stop Criteria, or when budget is exhausted.

## Pre-Autonomy Gate

Before long unattended execution:

- existing project understanding completed when workspace is non-blank,
- vision canon approved or explicitly delegated,
- decision map has owners,
- autonomy contract exists,
- excellence horizon exists,
- user briefing skeleton exists,
- task queue has executable units,
- recovery policy is enabled.
- hard-stop boundaries are narrow and explicit,
- the system has permission to generate and execute high-EV improvements without asking.

If the user wants to skip deep alignment, record that choice and its risks.
