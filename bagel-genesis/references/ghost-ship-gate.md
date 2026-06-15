# Ghost Ship Integration Gate

Use this only when `.bagel/artifact_profile.yaml` marks the artifact as `software_product`, `existing_software`, or a mixed artifact with an interactive/runtime software module. For research, writing, documents, decks, and data analysis without an app/runtime surface, use the equivalent skeleton gate in `references/artifact-types.md` and record `skeleton_gate_passed_when_required` in `.bagel/gates/status.yaml`.

The S7 gate validates that the skeleton is genuinely runnable, not just a pile of files.

## Purpose

A Ghost Ship is a full-stack shell system that:
- Can boot
- Can navigate
- Can call stub APIs
- Can complete core journey with mock data
- Can run in the target runtime from the completion horizon
- All stubs have typed contracts
- All stubs are registered
- All core interfaces have contract tests

## Entry Conditions

Before running gate validation:

- [ ] Skeleton compiler finished (S6 complete)
- [ ] Product graph initialized when the project needs one (file-backed graph or UPMG)
- [ ] Stub registry generated (S6 complete)
- [ ] Contract schemas generated (S6 complete)
- [ ] Route map generated (S6 complete)
- [ ] Target runtime config generated when required by the completion horizon

## Verification Tool Rule

This skill does not assume the target project already has BAGEL scripts. For each condition, use the project's existing commands when available. If no verifier exists, create a small project-local verifier first and record it in `.bagel/ledger/gate-verifiers.md`.

Do not mark a condition as passed because a command is named in this document. A pass requires command output, browser evidence, test output, or a written manual inspection record with exact files checked.

## Exit Conditions (ALL Must Pass)

### Condition 1: App Boots in Target Runtime

Use the deployment target in `.bagel/completion_horizon.yaml`. If deployment is not part of the baseline deliverable, boot locally with the repo's normal dev/start command and verify HTTP 200 or a successful browser/app/CLI load.

**Pass:** Staging HTTP 200 when deployment is in the completion horizon; otherwise local server, browser, CLI, or app runtime evidence showing successful boot.
**Fail:** Target runtime cannot boot.

### Condition 2: All Product Routes Reachable

Run or create a route verifier for every route from the chosen product graph backend, route map, or inspected route definitions. If the stack has no route map, inspect route definitions and write `.bagel/evidence/routes-S7.md` listing each route, file, and reachability result.

**Pass:** 100% of routes accessible
**Fail:** Any route dead-end

### Condition 3: All API Contracts Have Tests

For each file in `.bagel/contracts/`, verify a corresponding contract test or runtime validation test exists. Record the mapping in `.bagel/evidence/contracts-S7.md`.

**Pass:** 100% of contracts have tests
**Fail:** Any contract without test

### Condition 4: All Contract Tests Pass

Run the repo's narrowest contract-test command. If none exists, create one or write a minimal test for each contract before passing the gate.

**Pass:** 100% contract test pass rate
**Fail:** Any failure

### Condition 5: All Stubs Registered with Typed Schemas

Inspect `.bagel/stubs/` and the code paths that call stubs. Every stub must have an ID, owner, typed schema, replacement criterion, and expiration policy. If this is repetitive, create a project-local stub registry verifier.

**Pass:** 100% stub registration
**Fail:** Any unregistered stub

### Condition 6: All Critical Stubs Have Expiration Policy

List critical stubs and verify each has an expiration date or explicit baseline/final-candidate acceptance record.

**Pass:** 100% of critical stubs have expiration
**Fail:** Any critical stub without expiration

### Condition 7: Global Error Boundary Works

```bash
# Trigger error in app
# Verify error boundary catches it
# Verify user sees graceful error UI
```

**Pass:** Errors caught by boundary
**Fail:** Uncaught errors crash app

### Condition 8: Auth Boundary Can Be Instantiated

```bash
# Verify auth middleware loads
# Verify protected routes redirect when unauthenticated
# Verify authenticated routes work
```

**Pass:** Auth boundary functional
**Fail:** Auth failures

### Condition 9: Core Ghost User Journey Completable

Run a browser, integration, or CLI scenario that completes the core journey with mock data. If no scenario exists, create the minimal scenario before passing S7.

**Pass:** Journey completes end-to-end
**Fail:** Any step fails

### Condition 10: No Hard Coherence Gate Violations

Evaluate every hard gate in `.bagel/coherence_rules.yaml`. Prefer automated checks; otherwise write a manual evidence table with gate, inspected files, result, and reason.

**Pass:** Zero violations
**Fail:** Any violation

## Failure Handling

### Contract Failure
- **Cause:** API contract mismatch
- **Action:** Return to S6, regenerate contracts
- **Log:** `.bagel/s7_failures/contract_failures.md`

### Route Dead End
- **Cause:** Route exists but no links
- **Action:** Repair route graph or route-map artifact
- **Log:** `.bagel/s7_failures/route_failures.md`

### Unregistered Stub
- **Cause:** Stub created but not in registry
- **Action:** Return to S6, register stub
- **Log:** `.bagel/s7_failures/stub_failures.md`

### Auth Boundary Missing
- **Cause:** Auth middleware not set up
- **Action:** Return to S6, implement auth boundary
- **Log:** `.bagel/s7_failures/auth_failures.md`

### Target Runtime Boot Failure
- **Cause:** App fails to start in target runtime
- **Action:** Debug, return to S6 if needed
- **Log:** `.bagel/s7_failures/boot_failures.md`

## Validation Report

After gate run, generate `.bagel/s7_report.md`:

```yaml
gate_report:
  timestamp: ISO-8601
  conditions_total: 10
  conditions_passed: 9
  conditions_failed: 1
  
  failures:
    - condition: 5
      description: "Critical stub missing expiration"
      details: "STUB-AI-001 has no expiration date"
      action: "Return to S6"
  
  verdict: BLOCKED
  
  next_steps:
    - "Fix stub expiration"
    - "Re-run gate validation"
```

## Hard Gate

**Ghost Ship Gate is a HARD GATE.** Value slice filling cannot begin until all 10 conditions pass. After repeated failures, repair S6, amend scope through S14, stop, or fork; do not skip this gate.

## Common Pitfalls

### Pitfall 1: Faking the Test
Symptom: Test exists but doesn't actually verify
Fix: Write meaningful assertions

### Pitfall 2: Mocking Too Much
Symptom: All data is mocked, nothing real
Fix: At least one real endpoint should work

### Pitfall 3: Skipping Auth
Symptom: Protected routes are unprotected
Fix: Always implement auth in skeleton

### Pitfall 4: No Error Boundary
Symptom: Errors crash app
Fix: Implement React Error Boundary or equivalent

## Quick Validation

If S7 will be rerun often, create a project-local one-command gate checker. Until then, the validation report plus recorded commands/evidence is the gate artifact.
