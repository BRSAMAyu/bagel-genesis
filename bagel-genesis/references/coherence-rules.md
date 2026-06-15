# Coherence Rules Reference

Definitions and examples for Hard Gates, Soft Gates, and Advisory rules.

## Rule Classification

| Detector Type | Example | Enforcement |
|---------------|---------|-------------|
| `deterministic_static` | design tokens, component API, routes | hard_gate |
| `deterministic_runtime` | no dead routes, form validation, API contract | hard_gate |
| `heuristic_runtime` | DOM density, interaction count, screenshot layout | soft_gate |
| `llm_review` | "feels like cheap admin panel" | advisory |
| `human_review` | High-taste judgment | checkpoint |

## Hard Gates (Deterministic, Non-Negotiable)

Hard gates have unambiguous detection algorithms. Violation = immediate block.

### UI Hard Gates

```yaml
- id: HG-COLOR-TOKEN-001
  description: "All colors must use design tokens"
  detector: static_analysis
  check: "grep for hex colors in src/**/*.{tsx,css}"
  block_on: any_unpinned_hex_color

- id: HG-COMPONENT-001
  description: "All buttons must use shared Button component"
  detector: static_analysis
  check: "grep for <button in src/**/*.tsx (excluding Button.tsx)"
  block_on: any_raw_button_element

- id: HG-ACTION-DENSITY-001
  description: "Primary actions per screen ≤ 3"
  detector: static_analysis
  check: "count primary buttons in each route"
  block_on: count > 3

- id: HG-CONFIRM-001
  description: "Destructive actions require confirmation modal"
  detector: static_analysis
  check: "find delete/remove handlers without ConfirmDialog wrapper"
  block_on: any_unwrapped_destructive_action
```

### API Hard Gates

```yaml
- id: HG-CONTRACT-001
  description: "All API endpoints must have schema contract"
  detector: static_analysis
  check: "verify .bagel/contracts/ has entry for each /api/* route"
  block_on: any_route_without_contract

- id: HG-AUTH-001
  description: "Protected routes must have auth guard"
  detector: static_analysis
  check: "find routes without auth middleware"
  block_on: any_protected_route_without_guard

- id: HG-ERROR-HANDLING-001
  description: "Async actions must have loading/error/retry states"
  detector: static_analysis
  check: "verify all async handlers have try/catch and loading state"
  block_on: any_async_without_error_handling
```

### Data Hard Gates

```yaml
- id: HG-OWNER-CHECK-001
  description: "User data access requires owner check"
  detector: static_analysis
  check: "find DB queries on user data without WHERE userId = ?"
  block_on: any_query_without_owner_check

- id: HG-INPUT-VALIDATION-001
  description: "All API inputs must be validated with schema"
  detector: static_analysis
  check: "find request handlers without Zod/schema validation"
  block_on: any_unvalidated_input
```

### Stub Hard Gates

```yaml
- id: HG-STUB-REGISTRATION-001
  description: "All stubs must be registered"
  detector: registry_check
  check: "verify the declared stub registry under .bagel/stubs/ has all stubs (YAML, JSON, Markdown table, or SQLite are valid if documented)"
  block_on: any_unregistered_stub

- id: HG-STUB-EXPIRATION-001
  description: "Critical stubs must have expiration policy"
  detector: registry_check
  check: "verify all critical stubs have expiration date"
  block_on: any_critical_stub_without_expiration
```

## Soft Gates (Heuristic, Configurable)

Soft gates use heuristics. Violations generate warnings, not blocks.

```yaml
- id: SG-DOM-DENSITY-001
  description: "DOM density per screen"
  detector: runtime_analysis
  check: "count interactive elements per route"
  threshold: 15
  warn_on: count > 15
  escalate_on: count > 30

- id: SG-VISUAL-NOISE-001
  description: "Visual noise (color count, gradient count)"
  detector: screenshot_analysis
  check: "analyze screenshots for color variety and complexity"
  threshold: medium
  warn_on: high

- id: SG-COPY-LENGTH-001
  description: "Copy length on key screens"
  detector: static_analysis
  check: "word count per screen"
  threshold: 100
  warn_on: count > 200
```

## Advisory (LLM/Human Review)

Advisory rules require human or LLM judgment. Used in checkpoints.

```yaml
- id: ADV-GENERIC-FEEL-001
  description: "Product feels generic (not distinctive)"
  reviewer: llm
  prompt: "Does this product feel distinctive or generic? Explain."

- id: ADV-COPY-TONE-001
  description: "Copywriting tone matches taste kernel"
  reviewer: llm
  prompt: "Does this copy align with warm, concise, non-intrusive tone?"

- id: ADV-EMOTIONAL-MATCH-001
  description: "Emotional resonance with target users"
  reviewer: human
  prompt: "How would target users feel using this?"

- id: ADV-PREMIUM-FEEL-001
  description: "Premium product feel"
  reviewer: llm
  prompt: "Does this feel like a premium product or a cheap prototype?"
```

## Rule Schema

Every rule has:

```yaml
rule:
  id: HG-XXX-NNN
  description: "..."
  detector_type: deterministic_static | deterministic_runtime | heuristic_runtime | llm_review | human_review
  enforcement: hard_gate | soft_gate | advisory | checkpoint
  check: "how to detect"
  block_on: "what triggers block (for hard gates)"
  warn_on: "what triggers warning (for soft gates)"
  escalate_to: "next-level reviewer (for soft gates)"
```

## Adding Custom Rules

Project-specific rules go in `.bagel/coherence_rules_custom.yaml`:

```yaml
custom_rules:
  - id: HG-CUSTOM-001
    description: "All AI responses must show confidence score"
    detector_type: deterministic_static
    enforcement: hard_gate
    check: "verify AI response components include confidence display"
    block_on: any_ai_response_without_confidence
```

## Verification Procedure

### Running Hard Gates

```bash
# Prefer an existing project-local coherence guard.
# If none exists, inspect each hard gate and write .bagel/evidence/coherence-hard.md.
```

### Running Soft Gates

```bash
# Prefer an existing project-local soft-gate check.
# If none exists, write advisory findings to .bagel/reviews/coherence-soft.md.
```

### Running Advisory

Dispatch LLM subagent for each advisory rule against current state.
