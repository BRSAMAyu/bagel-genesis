# User Simulation Protocol

Three-tier simulation/review protocol for verifying artifact experience. Use Playwright/Appium examples only for software or mixed artifacts with an interactive runtime. For research, writing, decks, documents, and data analysis, replace route/UI checks with the profile-specific deterministic checks in `references/artifact-types.md` and `references/state-machine.md`.

## Level 1: Deterministic Simulation

**Runs:** Every patch
**Latency:** < 30 seconds
**Tooling:** Playwright/code-based for software; structured inspection/check scripts/manual evidence table for non-software.

### What It Checks

Software checks:

```text
- All routes/commands/screens accessible (no dead-ends)
- All buttons/controls have accessible names
- All forms have validation
- All async actions have loading/error/retry states
- All protected routes enforce auth
- No console errors on page load
- No unhandled promise rejections
```

Non-software checks:

```text
- Research: claims link to evidence, methods/limitations present, citations resolve
- Writing: continuity, voice, pacing, outline fit, unresolved markers tracked
- Document/deck: render/export, layout overflow, hierarchy, factual consistency
- Data analysis: provenance, validation, reproducibility, chart/table correctness
```

### Software Implementation Example

```typescript
// tests/l1_simulations/deterministic.spec.ts
import { test, expect } from '@playwright/test';

test('all routes accessible', async ({ page }) => {
  const routes = await getRoutesFromProductGraphOrRouteMap();
  for (const route of routes) {
    const response = await page.goto(route);
    expect(response?.status()).toBeLessThan(500);
  }
});

test('no dead-end navigation', async ({ page }) => {
  // For each route, verify at least one navigation option
});

test('forms have validation', async ({ page }) => {
  // For each form, verify validation works
});
```

### Output

`.bagel/simulations/l1_report.json`:
```json
{
  "timestamp": "2026-06-15T14:00:00Z",
  "total_checks": 24,
  "passed": 24,
  "failed": 0,
  "duration_seconds": 12
}
```

---

## Level 2: Generated Scenario Scripts

**Runs:** Per value slice
**Latency:** 1-5 minutes
**Tooling:** Playwright, AI-generated specs

### How Scenarios Are Generated

The L2 system reads the chosen graph/backend/artifact map and generates scenario scripts or inspection tasks:

1. **Read value slice** from `.bagel/slices/`, `.bagel/product_graph.yaml`, or UPMG
2. **Extract expected user journey, reader path, research trace, deck narrative, or analysis path**
3. **Map actions or checks to UI locators, commands, sections, claims, slides, chapters, or pipeline steps**
4. **Generate Playwright spec, checklist, script, or review task appropriate to the artifact profile**
5. **Dry-run against the target runtime/form**
6. **Verify spec/check covers required graph records or artifact nodes**
7. **Execute scenario or inspection**
8. **Write result to simulation ledger**

### Example Generated Spec

```typescript
// Generated: 2026-06-15 for VS-001 (First Reflection Loop)
// Coverage: PB-FIRST-VALUE-IN-3MIN, PB-LOW-COGNITIVE-LOAD

test('new_user_first_reflection', async ({ page }) => {
  // Setup
  await page.goto('/onboarding');
  
  // Step 1: Welcome screen
  await expect(page.locator('h1')).toContainText('Welcome');
  await page.click('[data-testid="get-started"]');
  
  // Step 2: First reflection prompt
  await page.click('[data-testid="start-reflection"]');
  
  // Step 3: Voice or text input
  await page.fill('[data-testid="text-input"]', 'Today I felt...');
  await page.click('[data-testid="submit"]');
  
  // Step 4: Reflection card appears
  await expect(page.locator('[data-testid="reflection-card"]')).toBeVisible();
  
  // Step 5: Verify value delivered
  await expect(page.locator('[data-testid="insight"]')).toBeVisible();
});
```

### Scenario Types

Generated scenarios cover:
- Happy path (golden path)
- Error path (network failure, AI timeout)
- Empty state (no data)
- Permission denied
- Form validation
- Cancel/abandon
- Recovery from failure

### Output

`.bagel/simulations/l2_reports/{slice_id}_report.json`:
```json
{
  "slice_id": "VS-001",
  "timestamp": "2026-06-15T14:00:00Z",
  "scenarios_total": 8,
  "scenarios_passed": 7,
  "scenarios_failed": 1,
  "failures": [
    {
      "scenario": "ai_timeout_recovery",
      "error": "No retry button visible after timeout",
      "product_graph_record": "INT-AI-TIMEOUT-001",
      "severity": "P1"
    }
  ]
}
```

---

## Level 3: Async Shadow User Simulation

**Runs:** Milestones only
**Latency:** 5-30 minutes
**Tooling:** AI-driven, persona-based

### When to Run

- After Ghost Ship (S7)
- After core P0 slices complete
- Before Baseline Candidate (S15)

### How It Works

1. **Dispatch L3 subagent** with persona description
2. **Subagent explores product** as that persona
3. **Subagent reports**:
   - Confusion points
   - Missing features
   - Emotional responses
   - Suggestions

### Persona Examples

```yaml
persona_anxious_first_time_user:
  description: "22-year-old college student, anxious about privacy"
  context: "Never used AI reflection tools"
  expectations: "Wants reassurance about data safety"
  
persona_busy_professional:
  description: "35-year-old executive, time-constrained"
  context: "Has 5 minutes between meetings"
  expectations: "Wants value in < 2 minutes"
  
persona_skeptical_of_ai:
  description: "45-year-old engineer, skeptical of AI"
  context: "Reads about AI hallucinations"
  expectations: "Wants transparency about AI limitations"
  
persona_elderly_user:
  description: "70-year-old retiree, low tech literacy"
  context: "Uses iPhone, hesitant with new apps"
  expectations: "Wants clear, large text and simple flow"
```

### L3 Subagent Prompt

```markdown
You are simulating a user persona for {product_name}.

## Your Persona
{persona_description}

## Your Context
{persona_context}

## Your Task

1. Approach the product at {target_runtime_url_or_command} as this persona would
2. Try to accomplish the core user journey
3. Note:
   - Moments of confusion
   - Where you'd want more information
   - Emotional responses (frustrated, delighted, anxious)
   - What would make you abandon the product
4. Report findings

## Constraints

- Don't assume knowledge the persona wouldn't have
- React authentically as this persona
- Don't try to "succeed" - try to be the persona

## Output Format

```yaml
l3_report:
  persona: {persona_name}
  timestamp: ISO-8601
  journey_completed: false
  abandonment_point: "Onboarding step 3"
  
  confusion_points:
    - location: "First screen"
      issue: "Not clear what app does"
      severity: P0
      
  missing_features:
    - feature: "Privacy explanation"
      severity: P0
      
  emotional_responses:
    - moment: "First AI response"
      emotion: "delighted"
      reason: "Personalized insight felt valuable"
      
  suggestions:
    - "Add 'Why we ask for this' tooltip on sensitive inputs"
    
  overall_verdict: "Promising but onboarding needs work"
```
```

### Blocking Conditions

L3 simulations block milestone transitions if:

- Core journey impossible for any P0 persona
- Privacy understanding failure
- No actionable entry point
- Severe misleading interaction
- Critical emotional mismatch

Non-blocking findings:
- Minor confusion
- Polish suggestions
- Aesthetic preferences

---

## Integration with State Machine

- **S10:** L1 runs on every patch (blocking)
- **S11:** L2 runs per slice (blocking)
- **S12:** L3 runs at milestones (selectively blocking)

## Failure Recovery

If simulation fails:
1. Identify failing scenario
2. Trace to product graph record or UPMG node
3. Fix implementation
4. Re-run simulation
5. Document in `.bagel/simulations/retry_log.md`
