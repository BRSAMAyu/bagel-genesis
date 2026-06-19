# Autonomous Researcher — the two styles

`autonomous_researcher` (Mode 2) is the *independent scientist* mode. Unlike
`protocol_execution` (Mode 1), where the user hands over a fixed protocol and BAGEL
executes it with maximal rigor, here BAGEL is trusted to do creative scientific work.
That trust splits into two very different jobs — divergent and convergent research —
with opposite freedom/safety profiles. A run declares exactly one:

```yaml
research_autonomy:
  mode: autonomous_researcher
  objective: discovery | optimization
```

The shared governance (preregistration of any *confirmatory* claim, amendment
records, drift limits, R3/R4 referee, the Mode-1 rigor stack) still applies the
moment a claim becomes load-bearing. What the two styles change is *what the agent
is trying to produce* and *what it is allowed to touch*.

---

## Style A — Explorer (`objective: discovery`)

**Job:** the user gives a vague, open-ended direction and wants back a small set of
*genuinely novel, genuinely useful, self-validated* ideas — directions worth their
own real project later. The user explicitly does **not** want the agent to touch or
risk their actual project. Output is **vetted ideas, never commits to the user's
code.**

**Contract:**

```yaml
discovery_contract:
  direction: "explore the internal mechanism of where LLMs err on long-horizon agent tasks"
  deliverable: vetted_ideas
  blast_radius: sandbox_only            # HARD: may not modify the user's real project
  sandbox_path: ".bagel/explore/"       # or a git worktree under .bagel-worktrees/
  novelty_bar: "must articulate a delta vs known work it can name"
  idea_budget: 5                        # how many vetted ideas to return
  forbidden_directions: []              # taste/scope guard from the user
```

### The discovery loop

Raw idea generation is *not* the weak point (a pinned-lens Brainstormer already
produces expert-level ideas — see RUN-001). The weak points are **taste** (framing +
selection) and **self-validation** (an idea backed by a cheap experiment beats an
idea merely asserted). The loop operationalizes both:

0. **Frame** → `.bagel/explore/discovery-frame.yaml`. Turn the vague direction into a
   *map*: decomposed open sub-questions, what is already known (priors), what a
   "valuable novel finding" looks like *here*, the novelty bar, idea budget, and
   forbidden directions. This is the taste-setting step; skipping it is why agents
   wander. Without a frame, generation has no target and selection has no rubric.

1. **Diverge** → dispatch ≥3 Brainstormers with *distinct* research lenses (see
   below) + a Product Visionary for paradigm-level reframes. Each idea records its
   lens, the claim, why it might be true, and what it would explain or enable.
   Diversity is enforced: ideas from the same lens that restate each other are
   merged; an idea is kept only if it surfaces something a *different* lens did not.

2. **Ground novelty** → for every surviving idea, a `novelty_record`: what is
   *already known/done* (name the related work — use web search when available, else
   reason explicitly and flag the uncertainty), what is *specifically new* here, why
   it is *different* (not a rename of a known method), and the honest *risk it has
   already been done*. An idea that cannot state its delta against work it can name
   is demoted, not reported. This is what makes the idea **self-validated as novel**
   rather than novel-sounding.

3. **Cheap-probe** → for each top idea, design and run *the cheapest experiment that
   updates belief* — a smoke test, a minimal measurement, a toy reproduction — **in
   the sandbox only**. Record `probe: {command, result, belief_update}`. This is what
   makes the idea **self-validated as promising**: the agent does not just assert the
   idea is good, it runs something cheap and reports what moved. A probe that touches
   anything outside the sandbox is a contract violation.

4. **Select by taste** → route survivors through the Judgment Council on the
   discovery dimensions: **novelty** (genuinely new?), **usefulness** (would the
   researcher actually care?), **evidence** (did the probe support it?),
   **tractability** (could it be pursued without heroics?). Rank; keep the top
   `idea_budget`. Council `strong_no` on novelty or usefulness vetoes.

5. **Report** → `.bagel/explore/discovery-report.yaml`: the ranked vetted ideas, each
   carrying its frame-link, novelty record, probe evidence, council verdict, and the
   **falsifiable next experiment** the researcher could run to pursue it. Plus an
   honest **"considered but did not pursue, and why"** section — the negative space is
   part of good research taste. Zero changes to the user's real project.

### Research lenses (Explorer)

Beyond the generic Brainstormer lenses, discovery uses research-specific lenses so
the spread covers the ways a real finding can hide:

- **mechanism** — *why* does the phenomenon happen; what internal process produces it
- **intervention** — what change would causally move it (and thereby reveal it)
- **measurement** — what new way of measuring would make the invisible visible
- **failure-mode** — where/when does the system break, and what does the break expose
- **analogy-transfer** — what known result from an adjacent field maps here
- **theoretical-frame** — what model/abstraction would make the messy facts simple
- **scaling** — how does it change with size/length/compute, and what does that imply

### The safety property (enforced)

`blast_radius: sandbox_only` is the user's #1 ask and is *mechanically enforced*, not
trusted. Across a discovery run, no file outside the sandbox path and `.bagel/` may be
created or modified. This is checked by `scripts/discovery_sandbox_check.py` (against
the file-write attestation log when available, else git scope) and can be hard-blocked
at the tool boundary by the opt-in control-plane guard. The point: an Explorer run
*cannot* screw up the real project, by construction — not by good behavior.

The report-integrity property is also enforced: every idea in `discovery-report.yaml`
must carry a non-empty novelty record, a probe with a real `result`, a council
verdict, and a falsifiable next step. A bare-assertion idea cannot enter the
deliverable. This is what makes "creative" also mean "rigorous."

---

## Style B — Optimizer (`objective: optimization`)

**Job:** the user has a method and wants the best possible score on named
benchmark(s). The agent may improve *how* the method is implemented, swap components,
or even find a **better method than the user's** — but every point of gain must be
*real*: held-out, leakage-free, statistically honest, and attributable to a genuine
method change rather than to overfitting the measurement.

An optimizer pointed at a benchmark score is the textbook setup for the worst
research-integrity failures (test leakage, validation overfit, seed cherry-picking,
"improving the measurement, not the method"). So Style B is **not** lighter than Mode
1 — it is Mode 1's *full* rigor stack (`statistical_rigor_check`, `data_leakage_check`,
`reproducibility_checklist_check`, R3/R4 referee) **plus** an optimization loop with
its own anti-gaming gate. The freedom is in the *method*; the rigor on the *number* is
absolute.

**Contract:**

```yaml
optimization_contract:
  targets:
    - benchmark: "GSM8K"
      metric: "accuracy"
      goal: maximize                    # maximize | minimize
      current_baseline: 0.82            # the user's method's current score (the bar to beat)
      split_policy: select_on_val_test_once
  method_latitude: may_replace_method   # may_tune | may_swap_components | may_replace_method
  integrity: inherits_mode1_full        # statistical_rigor + data_leakage + reproducibility + referee
  honest_denominator: true              # every variant tried is logged, not just the winner
```

### The optimization loop

0. **Lock target** → `.bagel/research/optimization-target.yaml`: benchmark(s), metric,
   current baseline score, and the split policy (**select on validation; touch test
   exactly once, at the end**). Written before any optimization — it is the bar and
   the rulebook.

1. **Diagnose** → error-analyze the baseline on *validation*. Where is it losing
   points? Record candidate levers (the high-leverage failure clusters).

2. **Propose variants** → through optimization lenses: *implement the user's idea
   better* (the user explicitly wants this), *swap a component*, or *propose an
   alternative method that might beat it*. Each variant is a hypothesis with an
   expected gain and the lever it attacks.

3. **Eval on validation, keep if better** → implement the variant in the sandbox,
   measure on **validation** (never test), keep it if it beats the current best. Loop.
   **Every variant tried is logged** — the winner is reported against the honest
   denominator of all attempts, so a gain that is really one-in-twenty noise is
   visible as such (and corrected for).

4. **Confirm once** → the single best method gets the **one** test-set evaluation,
   with multiple seeds, error bars, a significance test against the baseline, a
   leakage audit, and an **ablation that attributes the gain** to the specific change.
   This is the confirmatory claim — it must pass the full Mode-1 stack and an R3/R4
   referee. A gain that survives validation but not the held-out test, or that the
   ablation cannot attribute, is reported as such, not headlined.

5. **Report** → the improved method, the faithful before/after score with statistics,
   the ablation, and full reproducibility. If the agent found a genuinely better
   method than the user's, that is the headline — provided the number is real.

### The integrity property (enforced)

`scripts/optimization_integrity_check.py` (Optimizer's anti-gaming gate) requires:
the target + baseline declared *before* the optimization log has gains; every *kept*
improvement selected on validation (`selection_used != test`, reusing the
`data_leakage` policy); the honest denominator (all variants logged, multiple-
comparison correction once enough were tried); the final headline gain bound to the
Mode-1 confirmatory stack; and the gain *attributed* by ablation. A benchmark number
that improved by touching test, by val-overfitting, or by un-attributed luck cannot
become the headline.

---

## Why the split matters

Discovery maximizes *novelty × usefulness* under a **zero-blast-radius** safety
contract; optimization maximizes a *measured target* under an **absolute-integrity**
contract. They are the divergent and convergent halves of being a real independent
researcher. Forcing both through one mode would either over-constrain discovery
(you cannot preregister a hypothesis you are still searching for) or under-constrain
optimization (a score chaser with no leakage gate games the benchmark). Declaring the
`objective` up front routes each to the loop, the roles, and the teeth it actually
needs.

See also: `references/research-governance.md` (shared governance, Mode-1 rigor stack,
amendment records), `references/innovation-protocol.md` (exploration budget, concept
ledger), `references/taste-judgment.md` (Judgment Council), `references/breakthrough-search.md`
(non-local idea operators), `agents/research-explorer.md`, `agents/research-optimizer.md`, `agents/research-referee.md`.
