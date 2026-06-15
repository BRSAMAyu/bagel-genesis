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

## Run-Mode Depth

Use the lightest alignment depth that makes unattended work executable:

- `quick_autonomy`: one focused alignment pass, usually 10-20 minutes. Produce `.bagel/constitution.yaml` and enough `.bagel/state.yaml` to start the Build loop. Expand only when ambiguity blocks useful work.
- `full_genesis`: complete alignment package for blank-slate, multi-day, high-risk, or broad product takeover work.

Do not spend the first hours of a run producing governance documents when a bounded, reversible implementation or experiment can already produce evidence.

## Alignment Question Tree

Ask enough of these to make the next autonomous run safe and useful. Do not ask them mechanically; skip answers already supplied.

### Fast path (the 4 questions that carry ~80% of the value)

If the user is tired, time-constrained, or just wants to delegate fast, get crisp answers to these four and start. The rest can be inferred, defaulted, or asked only if a hard-stop ambiguity remains:

1. **Core vision** (Q1): What are we making, for whom, what pain does it solve?
2. **Disappointment** (Q3): What outcome would disappoint you even if it technically works? — this is the strongest single alignment signal.
3. **Hard-stops** (Q7): Which choices are true hard-stops I must wake you for (irreversible, paid, credentialed, production, legal/privacy, core identity)?
4. **Budget + return** (Q13 + Q14): How long may I run, and what do you want to see in STATUS.md when you wake?

Taste/exemplars (Q8/Q10) are high-value if the user has them ready, but if not, default to the constitution's taste kernel and surface style options in the morning briefing instead of guessing all night.

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
