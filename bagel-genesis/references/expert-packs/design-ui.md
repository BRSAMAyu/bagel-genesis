# Design UI Expert Pack

```yaml
expert_pack:
  artifact_type: design_ui
  top_1_percent_traits: [visual_hierarchy, rhythm, interaction_states, accessibility, identity, responsive_fit]
  common_amateur_failures: [generic_gradient, no_empty_states, weak_spacing, text_overflow, inaccessible_contrast, no_keyboard_nav, no_error_states]
  hidden_quality_dimensions: [scan_path, perceived_latency, motion_restraint, information_density, focus_management, aria_correctness]
  evaluation_traps: [single_screenshot, pretty_but_unusable, no_mobile, desktop_only_dark_mode]
  minimum_evidence: [desktop_screenshot, mobile_screenshot, interaction_state_check, accessibility_audit, keyboard_nav_check]
  useful_metrics: [contrast_passes, overflow_count, key_flow_completion, visual_diff_notes, axe_violations, lighthouse_score]
  qualitative_rubric: [hierarchy, rhythm, affordance, taste_fit, accessibility]
  red_team_questions: [Where does the eye go first?, What happens on error?, Does it still work on mobile?, Can a screen-reader user complete the flow?, What happens at 320px width?, Is keyboard navigation complete?]
  breakthrough_operators_to_prioritize: [constraint_as_feature, change_unit_of_optimization, expert_embarrassment_test]
  final_delivery_standard: "Screens are visually coherent, responsive, accessible, and interaction-complete."
```

## Design UI Methodology

### §1 — Accessibility is not optional (gate, not trait)
Accessibility is a hard gate, not a quality dimension. Before a UI slice is marked complete:
- **Contrast**: text contrast ratio ≥4.5:1 (WCAG AA) for normal text, ≥3:1 for large text. Record in non-functional-quality.yaml `accessibility.baseline.contrast_ratio_min`.
- **Keyboard navigation**: every interactive element is reachable and operable via keyboard alone (Tab/Shift-Tab/Enter/Space/Esc). Record `keyboard_nav_complete: true`.
- **Screen-reader labels**: every interactive element has an accessible name (aria-label, aria-labelledby, or visible text). Record `screen_reader_labels: true`.
- **Focus management**: focus moves logically (not trapped, visible indicator present).
A UI slice that fails any accessibility gate is not complete — it is a P1 finding.

### §2 — Responsive is not "works on desktop"
Test at minimum: 320px (mobile), 768px (tablet), 1280px (desktop). Record breakpoints tested and minimum width supported. Text overflow, horizontal scroll, and broken layouts at narrow widths are P1 findings.

### §3 — Interaction states are part of the design
Every interactive element must have designed states: default, hover, focus, active, disabled, error, loading, empty. A button without a disabled state is incomplete. Record interaction-state coverage in the evidence.

### §4 — Error and empty states
Every view must handle: data not loaded (skeleton/loading), data empty (empty state with guidance), error (error state with recovery action). A view that only works in the happy path is not shippable.

### §5 — Visual hierarchy and scan path
The eye should reach the primary action within 2 seconds. Test by asking: what does the user see first? If the answer is not the primary value/action, the hierarchy is wrong. Record the scan-path assessment.

### §6 — Motion restraint
Animation should guide attention, not decorate. Every animation must have a purpose (feedback, orientation, transition). Auto-playing motion that cannot be disabled violates accessibility (motion sensitivity). Respect `prefers-reduced-motion`.

### §7 — Evidence requirements (not just screenshots)
A UI slice's evidence must include: desktop screenshot (1280px), mobile screenshot (375px), keyboard-nav recording or checklist, and an accessibility audit (axe-core or equivalent). A single desktop screenshot is insufficient evidence — it hides mobile breakage and accessibility failures.
