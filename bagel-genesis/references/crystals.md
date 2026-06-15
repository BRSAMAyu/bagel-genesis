# Architecture Crystal Extraction

Extract reusable decision patterns from successful build experiences.

## What is a Crystal?

An Architecture Crystal is a crystallized decision pattern extracted from a completed build. It captures:

1. **Context:** The conditions under which this decision worked
2. **Decision:** The proven approach
3. **Anti-patterns:** What to avoid in similar contexts
4. **Applicability:** When this crystal applies
5. **Mutation requirements:** How to adapt for different contexts

## Why Not Just Reuse?

Crystals are not meant for blind adoption because:
- Context matters enormously
- What works for mobile-first may fail for desktop-first
- A pattern that works for one user type may fail for another
- Technology evolution changes what "works"

## Crystal Lifecycle

```
Build Experience → Crystal Extraction → Verification → Storage
                              ↓
                       Applicability
                         Check
                              ↓
                    Crystal-Informed
                    Decision Synthesis
```

## Crystal Schema

```yaml
decision_crystal:
  id: CRYSTAL-{DOMAIN}-{SEQUENCE}
  version: "1.0"
  created_at: ISO-8601
  
  domain:
    - ai_consumer_product
    - developer_tool
    - enterprise_software
    # etc.
  
  context:
    user_type:
      - emotionally_sensitive
      - technically_savvy
      - time_constrained
    platform:
      - mobile
      - web
      - desktop
    first_session_goal:
      - low_pressure_input
      - quick_value_demonstration
    team_size:
      - solo
      - small_team
      - large_team
  
  proven_decision:
    - title: "Dual input mode with voice-primary"
      description: "Voice as primary input with text fallback"
      rationale: "Users prefer speaking but need backup option"
      alternatives_rejected:
        - "Text-only: Users prefer speaking for reflection"
        - "Voice-only: Accessibility and context requirements"
      
    - title: "Staged AI response"
      description: "Show AI processing in stages"
      rationale: "Reduces perceived latency, sets expectations"
  
  anti_patterns:
    - "voice_only_first_screen"
    - "dense_onboarding_survey"
    - "abstract_dashboard_before_user_data"
  
  applicability_conditions:
    must_have:
      - personal_reflection_product
      - low_trust_first_session
      - sensitive_user_data
    
    nice_to_have:
      - ai_powered_feature
      - voice_input_capability
  
  mutation_required_if:
    - elderly_users: "Add larger touch targets and slower transitions"
    - desktop_first: "Reverse input order: text-primary, voice-secondary"
    - professional_workflow: "Remove 'warm' copy, use professional tone"
    - high_volume_users: "Batch processing instead of real-time"
  
  evidence:
    - decision_id: ADR-012
      outcome: "P0 value slice passed L3 simulation"
    - decision_id: ADR-015
      outcome: "No P0 red-team findings"
  
  confidence: high
  
  known_limitations:
    - "Tested only with English speakers"
    - "Voice input requires microphone permission"
```

## Extraction Procedure

### Step 1: Identify High-Quality Decision Chains

Look for:
- All P0 value slices passed
- No P0 red-team findings
- All L3 simulations passed
- User acceptance granted

### Step 2: Extract Decision Pattern

For each high-quality decision:

1. Document the decision (from ADR)
2. Document the context from the chosen product graph backend
3. Document the outcome (from simulations/red-team)
4. Document alternatives considered
5. Identify anti-patterns

### Step 3: Verify Applicability

Before storing, verify:

```yaml
verification:
  context_match_score: 0.85  # How well current context matches
  difference_scan:
    - "Current: mobile-first, Crystal: desktop-first"
    - "Current: 25-45 professionals, Crystal: 18-25 students"
  applicability_score: 0.7  # Adjusted for differences
  
  conclusion: "Applicable with mutations for desktop users"
```

### Step 4: Create Crystal File

```bash
mkdir -p .bagel/crystals
touch .bagel/crystals/CRYSTAL-AI-JOURNAL-FIRST-ENTRY.yaml
```

### Step 5: Store and Index

```bash
mkdir -p .bagel/crystals
# Add CRYSTAL-XXX.yaml and update .bagel/crystals/index.yaml if no registry exists.
```

## Crystal Storage

### Directory Structure

```
.bagel/crystals/
├── CRYSTAL-AI-JOURNAL-FIRST-ENTRY.yaml
├── CRYSTAL-VOICE-INPUT-FALLBACK.yaml
├── CRYSTAL-PRIVACY-FIRST-DESIGN.yaml
└── registry.json
```

### Registry

```json
{
  "crystals": [
    {
      "id": "CRYSTAL-AI-JOURNAL-FIRST-ENTRY",
      "domain": ["ai_consumer_product"],
      "created_at": "2026-06-15",
      "extracted_from": "Inner Cosmos v1.0"
    }
  ],
  "index": {
    "by_domain": {...},
    "by_context": {...}
  }
}
```

## Using Crystals

### In New Projects

Crystals are off by default for new projects unless the user or autonomy contract explicitly enables them.

1. Read relevant crystals from registry only after enablement.
2. For each crystal, run applicability check.
3. Route applicable crystals through Constitutional Court as imported prior-pattern evidence.
4. If accepted, synthesize decision.
5. Document mutations, assumptions, and rejected inherited assumptions.
6. Enter as new ADR only after Court approval or user approval.

Never import a crystal directly as an ADR. A crystal is evidence, not authority.

### Applicability Check Prompt

```markdown
Given a crystal and new project context:

Crystal: {crystal_yaml}
New Project Context: {context_yaml}

1. Calculate context match score (0-1)
2. Identify key differences
3. Determine mutation requirements
4. Assess applicability (applicable/not_applicable/requires_significant_mutation)
5. If applicable, what adaptations are needed?
```

## Crystal Anti-Patterns

### Blind Adoption
Problem: Copying crystal without checking context
Solution: Always run applicability verification

### Hidden Context Transfer
Problem: Importing a prior project's taste, user assumptions, or engineering compromises as "proven"
Solution: Treat every crystal as suspect prior-pattern evidence and route through Court before it affects decisions

### Context Inflation
Problem: Treating "nice to have" as "must have"
Solution: Distinguish between must/must not/nice to have

### Version Stagnation
Problem: Using outdated crystals
Solution: Version crystals and track evolution

## Integration with State Machine

- **S16b:** Crystal extraction happens after excellence-loop stabilization when applicable
- **Any project start:** Can consult crystal registry

## Quality Standards

A crystal must have:
- [ ] Domain tags
- [ ] Context description
- [ ] At least one proven decision
- [ ] At least two anti-patterns
- [ ] Applicability conditions
- [ ] Mutation requirements
- [ ] Evidence from build
