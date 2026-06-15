# Vision Constitution Template

Use this template to create `.bagel/constitution.yaml` (quick) or `.bagel/constitution.json` (full).

## Template

```json
{
  "product_name": "{product_name}",
  "version": "1.0",
  "created_at": "{ISO-8601 timestamp}",
  
  "north_star": {
    "one_sentence": "{One sentence describing what the product does and who it serves}",
    "core_value": "{The primary value this delivers to users}",
    "success_metric": "{How we measure success (qualitative or quantitative)}"
  },
  
  "target_users": {
    "primary": [
      "{Description of primary user 1}",
      "{Description of primary user 2}"
    ],
    "secondary": [
      "{Description of secondary user 1}"
    ],
    "excluded": [
      "{Who this product is NOT for}",
      "{Unacceptable use cases}"
    ]
  },
  
  "product_positioning": {
    "category": "{e.g., AI-powered reflection tool}",
    "differentiation": "{What makes this different from alternatives}",
    "analogies": [
      "{Product A meets Product B}"
    ]
  },
  
  "forbidden_directions": [
    "{Direction that would violate core purpose}",
    "{Approach that contradicts target users}",
    "{Feature that would drive wrong behavior}"
  ],
  
  "core_features": {
    "p0": [
      "{Must-have feature 1}",
      "{Must-have feature 2}"
    ],
    "p1": [
      "{Should-have feature 1}"
    ],
    "p2": [
      "{Nice-to-have feature 1}"
    ]
  },
  
  "autonomy_policy": {
    "system_can_decide": [
      "page_layout",
      "interaction_details",
      "data_structures",
      "api_design",
      "component_splitting",
      "default_empty_states",
      "test_cases",
      "technical_implementation"
    ],
    "human_checkpoint_required": [
      "core_positioning_change",
      "privacy_policy_change",
      "business_model_change",
      "removing_p0_features",
      "adding_unplanned_p0_features",
      "introducing_high_risk_dependencies",
      "target_user_scope_change"
    ],
    "system_must_inform": [
      "architectural_decisions",
      "third_party_service_selection",
      "performance_optimization_approach",
      "new_test_strategy"
    ]
  },
  
  "constraints": {
    "privacy": [
      "{Privacy requirement 1}",
      "{Privacy requirement 2}"
    ],
    "performance": [
      "{Performance requirement 1}"
    ],
    "accessibility": [
      "{Accessibility requirement 1}"
    ],
    "platform": [
      "{Platform requirement 1}"
    ]
  },
  
  "taste_boundaries": {
    "visual": {
      "direction": ["restrained", "premium", "calm"],
      "forbidden": ["neon", "excessive_animation", "cluttered"]
    },
    "interaction": {
      "direction": ["low_friction", "progressive_disclosure"],
      "forbidden": ["complex_forms", "mandatory_account_creation"]
    },
    "copywriting": {
      "direction": ["warm", "concise", "encouraging"],
      "forbidden": ["corporate", "over_motivational", "robotic"]
    }
  },
  
  "completion_criteria": {
    "minimum_viable": [
      "{Criterion 1}",
      "{Criterion 2}"
    ],
    "ready_for_users": [
      "{Criterion 1}"
    ],
    "ready_for_scale": [
      "{Criterion 1}"
    ]
  },
  
  "anti_patterns": [
    "{Pattern to avoid 1}",
    "{Pattern to avoid 2}"
  ]
}
```

## Examples

### Example 1: AI Reflection App

```json
{
  "product_name": "Inner Cosmos",
  "north_star": {
    "one_sentence": "An AI-powered self-reflection companion for busy professionals who want to understand themselves better",
    "core_value": "Helps users gain clarity through structured reflection and AI-generated insights",
    "success_metric": "Users who reflect at least 3x/week report increased self-awareness"
  },
  "target_users": {
    "primary": [
      "Busy professionals aged 25-45",
      "People interested in personal growth"
    ],
    "excluded": [
      "Users seeking therapy or mental health treatment",
      "Users who want productivity tools"
    ]
  },
  "forbidden_directions": [
    "Cannot become a social media platform",
    "Cannot show other users' reflections",
    "Cannot use gamification that creates anxiety"
  ],
  "autonomy_policy": {
    "human_checkpoint_required": [
      "showing reflections to others",
      "changing AI model",
      "adding social features"
    ]
  }
}
```

### Example 2: Developer Tool

```json
{
  "product_name": "DevFlow",
  "north_star": {
    "one_sentence": "A CLI tool that helps developers maintain flow state by reducing context switching",
    "core_value": "Minimizes interruptions while keeping critical notifications",
    "success_metric": "Users report < 2 interruptions per hour during deep work"
  },
  "target_users": {
    "primary": [
      "Software developers",
      "Technical leads"
    ],
    "excluded": [
      "Non-technical users",
      "Users who need real-time collaboration"
    ]
  },
  "forbidden_directions": [
    "Cannot add social features",
    "Cannot become a project management tool",
    "Cannot require cloud account"
  ]
}
```

## Validation Checklist

When creating constitution, verify:

- [ ] `product_name` is non-empty
- [ ] `north_star.one_sentence` is one sentence
- [ ] `north_star.core_value` doesn't repeat one_sentence
- [ ] `target_users.primary` has at least one entry
- [ ] `target_users.excluded` has at least two entries
- [ ] `forbidden_directions` has at least three entries
- [ ] `autonomy_policy.human_checkpoint_required` includes core_positioning_change
- [ ] `taste_boundaries` defines at least visual direction

## Constitutional Court Review

Before finalizing, run through Constitutional Court:

1. Is this internally consistent?
2. Do forbidden directions conflict with any feature?
3. Is autonomy policy clear enough for agents to self-govern?
4. Are taste boundaries specific enough to catch drift?

## Amendment Protocol

Constitution can be amended (see references/constitutional-court.md):
1. Propose change with rationale
2. Constitutional Court reviews
3. If approved, update version number
4. Cascade changes through the chosen product graph backend
