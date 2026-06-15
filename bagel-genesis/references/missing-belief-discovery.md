# Missing-Belief Discovery Taxonomy

Checklist taxonomy for discovering missing decisions during S3. This is not a code fuzzer unless a project-local analyzer is explicitly built.

## How to Use

For each relevant category below, ask: "Have we explicitly decided what to do when this happens?"

If the answer is "no" or "I'm not sure," generate a Missing Belief Card.

## Edge State Taxonomy

For every relevant interactive surface, data pipeline, research claim, document section, or async operation:

- `empty_state_for_every_list_view` — What does the user see when there's no data?
- `error_state_for_every_async_operation` — What if the operation fails?
- `loading_state_for_every_async_operation` — What shows during loading?
- `permission_denied_state_for_auth_action` — What if user isn't authorized?
- `network_failure_recovery_path` — What if network drops mid-operation?
- `timeout_recovery_path` — What if operation takes too long?
- `concurrent_modification_handling` — What if two users edit simultaneously?
- `offline_or_degraded_mode` — What if user is offline?
- `undo_or_cancel_path_for_destructive_action` — Can users recover?

## User Journey Taxonomy

For every entry point and flow:

- `first_time_user_entry_point` — Brand new user, no account, no data
- `returning_user_entry_point` — Existing user with history
- `re_engagement_after_dormancy` — User hasn't logged in for 30+ days
- `user_abandons_midway_path` — User closes browser mid-flow
- `user_goes_back_to_previous_step` — Back button behavior
- `user_makes_wrong_choice_path` — Wrong selection, how to recover
- `user_has_no_data_yet_path` — Onboarding state
- `user_has_too_much_data_path` — Power user with thousands of records

## Data Taxonomy

For every data display:

- `zero_records_case` — Empty dataset
- `single_record_case` — One item (special UI?)
- `large_dataset_case` — Pagination/virtualization needed
- `malformed_input_handling` — What if user pastes garbage?
- `unicode_and_special_characters` — Emojis, RTL, CJK
- `duplicate_records` — How to handle conflicts
- `stale_data` — Cache invalidation
- `partial_sync_failure` — Some records failed to sync
- `schema_migration_case` — Database schema changed

## Permission and Privacy Taxonomy

For every auth-gated feature:

- `unauthenticated_user_path` — Not logged in
- `authenticated_but_unauthorized_path` — Logged in, no permissions
- `owner_vs_non_owner_access` — Same resource, different access
- `delete_export_user_data_path` — GDPR/data deletion
- `sensitive_data_visibility` — Who can see what?
- `privacy_explanation_before_sensitive_input` — Before asking for SSN, etc.

## AI Pipeline Taxonomy

For every AI-powered feature:

- `ai_latency_longer_than_expected` — 10+ second responses
- `ai_timeout` — No response at all
- `ai_low_confidence_output` — Model is uncertain
- `ai_empty_output` — Model returns nothing
- `ai_malformed_json` — Model returns invalid JSON
- `ai_hallucinated_field` — Model invents fields
- `ai_safety_refusal` — Model refuses to answer
- `fallback_when_ai_unavailable` — Service is down

## Product Experience Taxonomy

For overall product feel:

- `first_value_under_3_minutes` — Can user get value quickly?
- `clear_primary_action` — Is the next step obvious?
- `text_fallback_for_voice_input` — Accessibility
- `low_cognitive_load_onboarding` — Not overwhelming
- `no_dead_end_after_failure` — Always a next step
- `clear_next_step_after_error` — Recovery path
- `mobile_responsive_breakpoints` — Works on phones
- `accessibility_compliance` — WCAG considerations

## Error Handling Taxonomy

For every error path:

- `client_side_validation_errors` — Form validation
- `server_side_validation_errors` — API rejects
- `unexpected_runtime_errors` — Crashes
- `database_errors` — DB issues
- `third_party_service_errors` — External API failures
- `rate_limiting_errors` — Too many requests
- `quota_exceeded_errors` — Usage limits

## Deployment & Operations Taxonomy

For production readiness:

- `environment_variables_missing` — Config issues
- `database_migration_failures` — Schema changes
- `cdn_or_asset_failures` — Static resources
- `feature_flag_failures` — Toggle issues
- `log_aggregation_gaps` — Observability holes

---

## Severity Classification

Each Missing Belief gets a severity:

- **P0 (Critical):** Blocks core user journey, security issue, data loss
- **P1 (Important):** Degrades experience, edge case crash, missing accessibility
- **P2 (Polish):** Nice-to-have, non-blocking

## Coverage Requirements

- **P0 Missing Beliefs:** Must be resolved before S5
- **P1 Missing Beliefs:** Must have decision (may defer implementation)
- **P2 Missing Beliefs:** Documented, may be deferred

## Generating Missing Belief Cards

For each identified gap:

```json
{
  "id": "MB-{CATEGORY}-{NUMBER}",
  "category": "edge_state",
  "type": "empty_state_for_list_view",
  "severity": "P1",
  "context": "User opens 'Recent Reflections' list with zero reflections",
  "question": "What should the user see?",
  "options": [
    "Onboarding prompt with example",
    "Sample reflections to explore",
    "Empty illustration with CTA"
  ],
  "recommendation": "Onboarding prompt with example",
  "recommendation_reason": "Aligns with low_cognitive_load and clear_primary_action principles",
  "confidence": "medium",
  "evidence_type": "industry_convention"
}
```

## Resolution Path

1. **Auto-resolve:** Industry convention with high confidence → become ADR
2. **Escalate:** User decision needed → checkpoint
3. **Variant:** Multiple viable options → generate variants for A/B
4. **Defer:** Low severity, document for later
