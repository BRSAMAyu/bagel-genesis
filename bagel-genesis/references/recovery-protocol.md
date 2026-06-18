# Recovery Protocol

Use when the run encounters severe bugs, tool failures, environment problems, design collapse, drift, or repeated review failures.

## Recovery Bias

Prefer autonomous repair, exploration, rollback, or switching tasks over stopping. Stop only for a hard-stop boundary in the autonomy contract or when all useful autonomous alternatives are exhausted and a checkpoint/resume plan exists.

Missing local tools, tests, verifiers, screenshots, benchmarks, fixtures, or experiment harnesses are not external blockers. Create or configure the smallest project-local capability needed to continue, then record the command and trust boundary. Treat this as normal recovery work.

## Recovery Ladder

1. **Local repair:** fix the immediate issue and rerun verification.
2. **Shrink scope:** create a smaller task that isolates the failing behavior.
3. **Diagnose independently:** dispatch reviewer/debugger with failing evidence only.
4. **Alternative path:** try a different implementation/design/research approach.
5. **Sandbox rework:** use worktree/sandbox for risky cascade changes.
6. **Rollback:** return to last known valid checkpoint and replay a safer plan.
7. **Re-plan:** update task queue and decision map.
8. **Switch lane:** advance another independent high-value task while the blocked lane is isolated.
9. **Capture lesson:** distill reusable evidence-backed learning into `.bagel/lessons/` or `ledger.yaml#lessons` before marking recovery complete.
10. **Escalate:** wake user only if required by hard-stop boundaries in the autonomy contract.

## Severe Drift

Signals:

- current work no longer serves the constitution,
- repeated local choices changed the product/artifact identity,
- user-facing briefing cannot explain why current work matters,
- reviewers find global incoherence,
- implementation constraints are driving product decisions.

Actions:

1. Stop only the drifting lane; continue safe independent work if possible.
2. Write `.bagel/ledger/drift-report.md`.
3. Compare current artifact to vision canon and constitution.
4. Identify last valid checkpoint.
5. Choose repair, rollback, fork, or amendment.
6. Use Constitutional Court for any scope/identity change.

## Environment and Tool Failures

Allowed autonomous repairs:

- inspect logs,
- install missing local dependencies if normal for the project,
- repair scripts/config,
- use alternative command,
- create minimal verifier when tool is absent,
- create browser/screenshot/layout checks when UI quality must be verified,
- create benchmark or experiment harnesses when research or optimization needs evidence,
- document external service outage,
- mock only when contract-backed and recorded.

Default rule for the gray zone: long-run delegation means the agent keeps moving. A repair that writes package/dependency manifests, lockfiles, environment files, CI config, deployment config, auth config, database config, or shared root config should **continue** whenever it satisfies any of: the autonomy contract pre-authorized that class of change; the change is small, reversible, and project-local (verifier, setup, dev dependency, config for a non-production target); or the change is isolated in a worktree/sandbox branch that can be discarded. Record the change in the evolution ledger and continue.

**Canonical hard-stop source:** the hard-stop boundary list in `SKILL.md` (the "Hard-stop boundaries" line) is the single authoritative enumeration. The expansion below names *when those same boundaries apply during recovery* — it MUST NOT reopen or conditionally weaken a SKILL.md hard-stop. In particular, **"pre-authorized" is not a generic escape hatch**: it means a specific `stop_contract` field the user filled interactively during Align (e.g. `stop_contract.pre_authorized.dependency_upgrades: [list]`), recorded in `.bagel/constitution.yaml` and shown to the user at the 🔴 CHECKPOINT · STOP CONTRACT. An agent-asserted `pre_authorized: true` boolean with no matching Stop Contract field is void (SKILL.md Anti-Patterns canonical-list rule).

Wake the user (hard-stop) only when an action crosses a true hard-stop boundary from the SKILL.md canonical list. The items below are hard-stops when they cross those boundaries. The "clears only via …" clauses name the exact Stop Contract field that can clear them — if that field is absent or unfilled, the hard-stop fires:

- using paid services or creating cloud resources — clears only via `stop_contract.pre_authorized.cloud_resources`,
- adding credentials, tokens, or external accounts — clears only via `stop_contract.pre_authorized.credentials`,
- running destructive migrations or deleting user data — clears only via `stop_contract.pre_authorized.destructive_migrations`,
- changing production infrastructure — never clearable from recovery (production is a canonical hard-stop),
- upgrading major dependencies or replacing frameworks — clears only via `stop_contract.pre_authorized.dependency_upgrades`,
- adding or upgrading dependencies that change lockfiles — clears only via `stop_contract.pre_authorized.dependency_upgrades`,
- editing `.env`, secrets files, package manager config, CI/deploy config, or root toolchain config — clears only via `stop_contract.pre_authorized.config_files`,
- mocking an external service in a way that could be mistaken for real integration,
- weakening security/privacy/legal guarantees — never clearable,
- force-pushing, rewriting history, or destructive git cleanup — never clearable (Anti-Pattern #10),
- installing system-wide tools outside the project,
- broad scope reduction or product/artifact identity changes — clears only via Constitutional Court (S14).

If a repair crosses a real hard-stop boundary, write a recovery option, continue with safe adjacent positive-EV work on other tasks, and surface the blocked decision in the user briefing. Do not idle.

## Repeated Failure Policy

Repeated failure does not mean stop. It means switch strategy or switch lane.

After three failures of the same kind (or three consecutive `lateral` progress deltas on the same approach):

- do not retry the same prompt,
- write a root-cause hypothesis,
- reduce the task,
- use independent diagnosis,
- attempt one alternative route,
- if still blocked, choose another positive-EV task or discovery lens,
- then decide whether a hard-stop boundary truly requires user input.

After any recovery ladder step 2 or higher, apply `references/lesson-memory.md`. A recovery is not complete until the agent either records a reusable lesson or records why the event was too local to be worth remembering.

### What counts as a strategy switch (not a parameter tweak)

A retry that only adjusts a value inside the same approach (a hyperparameter, a threshold, a wording change, a renamed variable) is the **same strategy** and still counts toward the three-attempt limit. A genuine strategy switch changes at least one of:

- the **approach** (e.g. greedy → dynamic programming; supervised → self-supervised; REST → event-driven),
- the **core assumption** (e.g. "users want speed" → "users want safety"; "single-tenant" → "multi-tenant"),
- the **artifact structure** (e.g. monolith → modular; one big PR → staged slices),
- the **evidence source** (e.g. unit tests → property tests; intuition → benchmark; one dataset → another).

If you cannot name what changed across at least one of those axes, you have not switched strategy — keep counting attempts. When in doubt, treat a borderline change as a parameter tweak and keep counting; this avoids gaming the counter to loop forever.

## User Wake Conditions

Wake the user when:

- irreversible or non-recoverable destructive action is needed,
- serious security/privacy/legal/financial/production-data risk would be introduced,
- external credentials, accounts, or paid access are required,
- production infrastructure or production data would be changed,
- core promise, target audience, business model, or research identity would change,
- an explicit user-forbidden boundary would be crossed,
- no useful autonomous path remains after recovery, rollback, alternative exploration, and independent task switching.

Otherwise continue, document, and brief.
