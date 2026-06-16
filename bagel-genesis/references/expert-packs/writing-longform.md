# Writing Longform Expert Pack

```yaml
expert_pack:
  artifact_type: writing_longform
  top_1_percent_traits: [premise_pressure, desire_conflict, scene_turns, voice, pacing, continuity, emotional_aftertaste]
  common_amateur_failures: [worldbuilding_loop, exposition_dump, flat_scene, inconsistent_voice, cliche]
  hidden_quality_dimensions: [subtext, escalation_shape, reader_question_management]
  evaluation_traps: [word_count, lore_volume, outline_completeness]
  minimum_evidence: [actual_prose_delta, scene_review, continuity_notes]
  useful_metrics: [scenes_completed, revision_delta, continuity_breaks_resolved]
  qualitative_rubric: [scene_turn, voice, pacing, emotional_aftertaste]
  red_team_questions: [What changes in this scene?, What does the character want?, Where is the tension?]
  breakthrough_operators_to_prioritize: [remove_assumed_requirement, constraint_as_feature, analogy_transfer]
  final_delivery_standard: "Produces actual polished prose, not just planning, with continuity and voice preserved."
```

## Longform methodology (mandatory procedure)

These procedures prevent the three failure loops: worldbuilding loop (planning forever, no prose), outline loop (re-outlining instead of revising prose), and word-count-as-quality (measuring length instead of scene-level quality).

### 1. Premise pressure test
Before writing, the premise must survive: "What changes in this scene that the reader cannot predict?" and "What does the protagonist want that they cannot easily get?" A premise where nothing changes or the want is frictionless is not a scene — it is an outline bullet. Reject it or raise the stakes.

### 2. Character desire/conflict matrix
For each viewpoint character, record: desire (what they want this scene), obstacle (what blocks it), stakes (what they lose if they fail), shift (how they change by scene end). A scene with no shift is a flat scene (`common_amateur_failures`). The matrix is the continuity source for multi-POV work.

### 3. Scene turn requirement
Every scene must have a turn — a reversal, revelation, or decision that changes the situation. A scene that ends where it began (same emotional state, same knowledge, same power balance) fails the turn check. This is the writing equivalent of a falsifiable hypothesis: if you cannot name the turn, the scene has no engine.

### 4. Anti-exposition-dump check
Backstory and worldbuilding are delivered through conflict and consequence, not through narration pauses. If a paragraph is pure description with no character agency or tension, it is an exposition dump (`common_amateur_failures`). Cut it or fold the information into a scene where someone needs it under pressure.

### 5. Voice sample lock
Lock a voice sample (2-3 sentences) per viewpoint character early. Every prose delta is checked against the voice sample — if the voice drifts (register, rhythm, diction), flag it. Inconsistent voice is a continuity break in longform.

### 6. Continuity ledger
Maintain a continuity ledger: timeline positions, character knowledge state (who knows what by when), physical positions, established facts. Each prose delta is checked against the ledger for contradictions. This is the writing equivalent of dataset integrity — a contradiction that survives to delivery is an unrecoverable defect.

### 7. First prose delta by cycle 2
By cycle 2, there must be actual prose (at least one scene in working draft), not just outline/worldbuilding. `evaluation_traps: outline_completeness` — an agent that delivers a perfect outline but zero prose has not done writing work.

### 8. Max outline-only cycles = 2
If 2 consecutive cycles produce only outline/worldbuilding changes with no prose delta, force a prose cycle. Do not let planning become procrastination.

### 9. Revision loop: scene-level over outline-level
Revision targets scenes (rewrite/restructure individual scenes), not the outline (re-planning the whole structure). Re-outlining during revision is the outline loop — it feels productive but produces no prose improvement.

### 10. Anti-cliche red-team pass
A red-team pass scans for cliches (stock phrases, predictable reactions, trope-compliant beats without subversion) and checks the emotional aftertaste (what feeling does the reader leave with — and is it the intended one?). Cliches and mismatched emotional aftertaste are quality defects even when the prose is grammatically clean.
