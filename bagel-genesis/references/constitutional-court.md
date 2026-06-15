# Constitutional Court Protocol

The Constitutional Court reviews amendment proposals to ensure they represent vision evolution, not engineering escape.

## Court Isolation Rules

The Court ONLY reviews:
- .bagel/constitution.yaml (quick) or .bagel/constitution.json (full) (original)
- `.bagel/taste_kernel.yaml` (original)
- `.bagel/completion_horizon.yaml` (current)
- Amendment proposal
- Simulation failures (if any)

The Court does NOT review:
- Current code complexity
- Executor failure count
- Library preferences
- Implementation difficulty
- Refactoring cost

## Who Can Propose Amendments

**Valid Proposers:**
- Human user
- Level 3 simulation failure (P0 severity)
- Constitutional Court flag from previous review

**Invalid Amendment Proposers:**
- Executor agent
- Patch agent
- Slice executor
- Engineering planner

**Rationale:** Executor agents may propose lowering vision to avoid difficult engineering problems. This must be blocked.

Executors may file an **escape report** when implementation pressure suggests a scope reduction. The Court may classify the report, reject it, or require explicit human approval. The Court must never directly accept implementation-originated scope reduction.

## Amendment Classification

### Type 1: Clarification
Scope: Adds specificity to existing provisions without changing direction.
Example: "Clarify that 'restraint' means no animations on first screen."
**Default:** Accept (no vision change)

### Type 2: Scope Expansion
Scope: Adds features or capabilities.
Example: "Add social sharing as a P1 feature."
**Default:** Accept with cost analysis

### Type 3: Scope Reduction
Scope: Removes features or simplifies.
Example: "Remove AI summarization from the baseline deliverable."
**Default:** Requires human approval **unless** the reduction is reversible, pre-authorized by the autonomy contract, and does not touch a P0 value slice or the core promise; in that case the Court may accept autonomously and record the decision, surfacing it in the user briefing.

### Type 4: Priority Change
Scope: Reorders feature importance.
Example: "Move offline mode to P1 from P2."
**Default:** Accept with updated horizon

### Type 5: Taste Change
Scope: Shifts visual/interaction direction.
Example: "Add darker color palette option."
**Default:** Accept with taste kernel update

### Type 6: Core Philosophy Change
Scope: Changes north star, target users, or core value.
Example: "Change from 'self-reflection' to 'social connection.'"
**Default:** Reject unless user-initiated

### Type 7: Privacy Boundary Change
Scope: Changes data handling or privacy approach.
Example: "Allow sharing reflections with friends."
**Default:** Requires human approval. Privacy is a hard-stop boundary; do not auto-accept even under delegation. While approval is pending, continue safe independent high-EV work and surface the blocked decision.

## Court Review Procedure

### Step 1: Classify Amendment

Determine amendment type from above.

### Step 2: Impact Analysis

For each amendment, assess:
- Alignment with original vision (yes/no/partially)
- Scope of change (local/slice/global)
- Reversibility (high/medium/low)
- Cascading effects (which nodes affected)

### Step 3: Engineering Escape Detection

Check for signs of engineering escape:
- Proposed changes make implementation "simpler"
- "Core" features are being deferred
- Complexity is cited as reason for change
- Workarounds being proposed as "improvements"

**If engineering escape detected:**
- Flag for human review
- Note: "This appears to avoid engineering difficulty rather than address user need"

### Step 4: Render Verdict

| Type | Default | Conditions |
|------|---------|------------|
| Clarification | Accept | - |
| Scope Expansion | Accept | Impact analysis complete |
| Scope Reduction | Human | If affects P0 |
| Priority Change | Accept | Horizon updated |
| Taste Change | Accept | Taste kernel updated |
| Core Philosophy | Reject | Unless user-initiated |
| Privacy Boundary | Human | - |

### Step 5: Document Decision

```yaml
constitutional_review:
  review_id: CCR-YYYY-NNN
  timestamp: ISO-8601
  amendment_id: AMEND-XXX
  amendment_type: scope_expansion
  classification_confidence: high
  
  analysis:
    aligns_with_vision: true
    engineering_escape_detected: false
    changes_core_promise: false
    affects_human_checkpoints: false
    
  impact:
    scope: slice
    reversibility: high
    affected_nodes: [VS-003, ADR-015]
    
  verdict: accept
  
  required_actions:
    - update_completion_horizon
    - update_product_graph_records
    - notify_user_if_affects_delivery
    
  rationale: "Expansion aligns with core value of 'reflection' and adds user value without changing vision boundaries."
```

## Court Prompt Template

```markdown
You are the Constitutional Court for a BAGEL Genesis project.

## Context

Product: {product_name}
North Star: {north_star}
Core Value: {core_value}

## Amendment Proposal

{proposal_text}

## Original Constitution

{constitution_json}

## Original Taste Kernel

{taste_kernel_yaml}

## Current Completion Horizon

{completion_horizon_yaml}

## Review Task

1. Classify the amendment type (1-7 from above)
2. Assess impact on vision alignment
3. Check for engineering escape evidence
4. Render verdict (accept/reject/require_human)
5. List required actions if accepted

## Output Format

Provide your review in the format specified in the Constitutional Court Protocol.
```

## Rejection Appeals

If an amendment is rejected, the human user can override:

```yaml
appeal:
  original_rejection: CCR-YYYY-NNN
  overrider: human_user
  rationale: "I understand the risk, but [reason]."
  conditions: [user-specified conditions]
```

Human override bypasses Constitutional Court but must be documented.

## Anti-Patterns to Flag

- "Let's simplify by removing X"
- "We can defer this to later"
- "The core functionality is the same"
- "This is just a technical detail"
- "Users won't notice the difference"
- "We can add it back later"

These phrases often signal engineering escape attempts.

## Integration with State Machine

- S1: Court reviews initial constitution
- S14: Court reviews all amendments
- Any state: Court can flag vision drift
