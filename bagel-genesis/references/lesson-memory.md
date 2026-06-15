# Lesson Memory Protocol

Use after recovery, repeated failures, environment/tool repairs, reviewer findings that recur, or any workaround likely to matter in a future run. The goal is to turn time spent failing into durable operational wisdom.

## Principle

`.bagel/` memory must store not only what changed, but what the system learned the hard way. A recovery event is not complete until reusable lessons have been considered.

Do not save chain-of-thought or long logs. Save compact, evidence-backed rules that a future agent can apply.

## Memory Layers

Use three layers:

```text
episode -> lesson -> playbook
```

- **Episode:** a concrete event, usually in recovery-log or progress delta.
- **Lesson:** a reusable rule with evidence and applicability.
- **Playbook:** a stable checklist or setup recipe promoted after recurrence.

## Canonical Files

Quick mode may store these inside `.bagel/ledger.yaml#lessons`; full mode uses:

```text
.bagel/lessons/
├── index.yaml
├── gotchas.yaml
├── environment.yaml
├── engineering.yaml
├── product.yaml
├── research.yaml
└── playbooks/
    └── <slug>.md
```

## Lesson Schema

```yaml
lessons:
  - id: "L-001"
    title: "Node OpenSSL legacy flag needed for current toolchain"
    layer: lesson | playbook_candidate
    category: environment | engineering | product | research | process | taste
    trigger:
      event: "npm install failed with ERR_OSSL_EVP_UNSUPPORTED"
      evidence: ".bagel/ledger/recovery-log.md#R-004"
    rule: "When running npm commands in this repo, set NODE_OPTIONS=--openssl-legacy-provider unless package lock changes remove the need."
    applies_when:
      - "node < 18 with legacy webpack"
    verification:
      command: "NODE_OPTIONS=--openssl-legacy-provider npm test"
      evidence: ".bagel/evidence/recovery/R-004/npm-test-pass.txt"
    confidence: high | medium | low
    promotion_count: 1
    status: active | superseded | rejected
    superseded_by: null
    created_at: "ISO-8601"
    last_confirmed_at: "ISO-8601"
```

## Capture Triggers

After each of these, run the Lesson Capture Checklist:

- recovery ladder step 2 or higher,
- same failure class occurs twice,
- local environment/tooling repair,
- dependency/setup workaround,
- reviewer finding repeats,
- a metric was gamed or replaced,
- a hypothesis failed in a way that changes future search,
- a user correction invalidates an assumption.

High frequency does not mean saving everything. Capture only if the lesson is likely to prevent future wasted work, protect a product promise, or improve future decision quality.

## Lesson Capture Checklist

For every trigger, decide:

1. Is this reusable beyond the current file edit?
2. Is there evidence for the rule?
3. Can a future agent detect when it applies?
4. Is it still safe to trust, or should it be re-verified first?
5. Should it remain a lesson, or be promoted to a playbook after recurrence?

If yes to 1-3, write or update a lesson before marking recovery complete.

## Using Lessons

At run start and before recovery:

1. Load `.bagel/lessons/index.yaml` or `.bagel/ledger.yaml#lessons`.
2. Select only lessons whose `applies_when` matches the current task.
3. Re-verify stale lessons when they affect safety, dependencies, environment, or architecture.
4. Apply active high-confidence lessons before rediscovering the same failure.

Prior `.bagel/` project context is a hint to re-verify, but lessons are stronger: they are evidence-backed operational rules. Trust them provisionally when `confidence: high` and `last_confirmed_at` is fresh; otherwise re-verify cheaply.

## Promotion

Promote a lesson to a playbook when either:

- it prevents the same failure twice, or
- it becomes part of normal setup/recovery for the project.

Playbooks must be short, command-oriented, and linked from `.bagel/lessons/index.yaml`.
