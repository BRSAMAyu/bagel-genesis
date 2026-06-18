# Run-Phase Model (authoritative)

Use whenever you set, read, or validate which phase a BAGEL run is in.

This file is the **single authoritative source** for phase vocabulary. It
replaces the previous situation where the same lifecycle was described by
three disjoint enums that an agent could not populate consistently.

## The problem this resolves

BAGEL historically carried three phase vocabularies that never reconciled:

1. `loop_binding.loop_phase` — binary `{align_protection, autonomous_build}` (enforced at `scripts/bagel_run_check.py`, referenced in `SKILL.md` Boot Sequence).
2. `state.phase` — five runtime values `{Build, Iterate, Polish, excellence_loop, complete}` (read by ~12 validator scripts).
3. `state-machine.md` — `S-2..S17` (+ `S16b`), never read by any script.

These value sets are disjoint. Setting `phase: Polish` did not set
`loop_phase`, and `Polish` is not even a legal `loop_phase` value. There was
no translation table. This file defines one.

## The single authoritative enum: `state.run_phase`

Record `run_phase` at the top level of `.bagel/state.yaml`. It is the
superset lifecycle that scripts and humans read:

| `run_phase` value | Meaning | Align gate passed? | Building? |
|---|---|---|---|
| `align` | Deep alignment, Stop Contract, calibration, evaluation/expert gates — Build not yet unlocked | no (or in progress) | no |
| `build` | Value-slice implementation loop under the run contract | yes | yes |
| `iterate` | Target set finished; generating next higher-value target set | yes | yes |
| `polish` | Baseline passes; positive-optimization excellence loop | yes | yes |
| `excellence_loop` | Multi-pass critique/ideation/bar-raise toward excellence horizon | yes | yes |
| `complete` | Final delivery accepted | yes | no |

`run_phase` is the field agents set and validators read. The two legacy
fields below are **derived views** computed from `run_phase` — keep them in
sync automatically, do not set them independently.

## Derivation rules (the reconciliation)

### `loop_binding.loop_phase` is derived from `run_phase`

`loop_phase` is the **autonomy-gate** view: has Build been unlocked?

| `run_phase` | `loop_phase` |
|---|---|
| `align` | `align_protection` |
| `build`, `iterate`, `polish`, `excellence_loop`, `complete` | `autonomous_build` |

Rule: `loop_phase = align_protection if run_phase == align else autonomous_build`. The loop may be bound during `align`, but only for Align/Resume protection — Build/Iterate before Stop Contract remains forbidden (SKILL.md Boot Sequence, Anti-Pattern #4).

### `state.phase` is derived from `run_phase`

`phase` is the **runtime-activity** view that the validator scripts read. It
is a synonym for `run_phase` with two cosmetic renames kept for script
back-compat:

| `run_phase` | `state.phase` (legacy alias scripts read) |
|---|---|
| `align` | `align` |
| `build` | `Build` |
| `iterate` | `Iterate` |
| `polish` | `Polish` |
| `excellence_loop` | `excellence_loop` |
| `complete` | `complete` |

Scripts that test `phase in {Build, Iterate, Polish, excellence_loop, complete}`
keep working unchanged. **Set `run_phase`; mirror it into `phase` and
`loop_phase`** so all three stay consistent. Do not set `phase` or
`loop_phase` to values that contradict the derivation table.

## S-state mapping (state-machine.md ↔ run_phase)

The `S-2..S17` IDs in `references/state-machine.md` are full-mode expansion
states, never read by scripts. They map to `run_phase` as follows, so a
full-mode agent always knows which runtime phase each S-state lives in:

| S-state | `run_phase` | Notes |
|---|---|---|
| S-2 Existing Project Intake | `align` | project understanding before any build |
| S-1 Deep Alignment | `align` | vision canon, autonomy contract, alignment floor |
| S0 Vision Intake | `align` | (records `vision_summary.md`, an input to S-1 depth) |
| S1 Constitution + Horizon | `align` | Stop Contract captured here; BUILD UNLOCK checkpoint fires at S1 exit |
| S2 Taste Kernel + Coherence | `align` | still pre-Build calibration |
| S3 Missing-Belief Discovery | `align` | pre-Build |
| S4 Product Graph Init | `align` | pre-Build setup |
| S5 Decision Classification | `align` | pre-Build setup |
| S6 Skeleton Era | `align` → `build` | skeleton is the last align-side artifact; value filling starts Build |
| S7 Skeleton/Ghost Ship Gate | `align` → `build` | gate that *authorizes* the `align`→`build` transition |
| S8 Value Slice Filling | `build` | (per-slice `iterate` when finishing a target set) |
| S9 Immediate Clearing | `build` | clears after each slice |
| S10 L1 Deterministic Verification | `build` | per-slice verification |
| S11 L2 Generated Scenarios | `build` | per-slice simulation |
| S12 L3 Shadow User Simulation | `polish` | milestone-level |
| S13 Counterfactual Red-Team | `polish` | |
| S14 Vision Amendment Check | any | can fire from any run_phase when an amendment is proposed |
| S15 Baseline Candidate | `polish` | entry into excellence loop |
| S16 Excellence Loop | `excellence_loop` | |
| S16b Crystal Extraction | `excellence_loop` | |
| S17 Final Delivery | `complete` | |

The `align`→`build` transition happens at the S7 Ghost Ship Gate, which is
the concrete firing point of the 🔴 CHECKPOINT · BUILD UNLOCK (see SKILL.md
Boot Sequence step 8). Until S7 passes, `run_phase` stays `align` and
`loop_phase` stays `align_protection`.

## Validation

`scripts/skill_lint.py` checks that:

- `run_phase` is documented here and in `SKILL.md`,
- `state-machine.md` carries the S-state → `run_phase` mapping,
- no file redefines `loop_phase` or `phase` value sets in a way that
  contradicts the derivation tables above.

If you need a guarantee that the three fields are consistent, set only
`run_phase` and let the derivation rules produce the other two.
