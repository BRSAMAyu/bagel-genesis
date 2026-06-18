# Enforcement Honesty (what the validators can and cannot guarantee)

Use when auditing the enforcement substrate, explaining a residual limit, or deciding whether a guarantee is mechanical or agent-attested.

This file is the canonical home for the semantic-integrity check inventory and the honestly-stated residual limits of the BAGEL enforcement substrate. It is loaded on demand (Loading Matrix row: `enforcement-honesty.md`), not at every activation, to keep SKILL.md's cold-start cost bounded.

## Semantic Integrity Checks (enforced by expert_strategy_check.py + production_surface_check.py)

These anti-cheat validators are unconditional for any non-lite run. They prevent the most common "form-satisfiable" shortcuts. The agent must populate the record files below to pass them — omitting a record does not skip the check.

| Check | Record file | What it catches |
|---|---|---|
| `validate_council_output` | councilor `output_ref` YAML | empty/placeholder verdicts, perspective/agent mismatch, verdict without evidence |
| `validate_premise_fidelity` | `.bagel/expert/problem-framing.yaml` → `premise_fidelity:` | proxy substitution without user consent, silent premise rewrite |
| `validate_named_dependency_protocol` | `.bagel/expert/named-dependency-protocol.yaml` | in-memory fallback for a named external dependency (scan: in_memory/fake_redis/mock_redis/hashmap) |
| `validate_dataset_integrity` | `.bagel/expert/dataset-integrity.yaml` | missing split hashes, no disjointness proof, test-set tuning, all-data preprocessing |
| `validate_requirement_coherence` | `.bagel/ledger.yaml` → `human_decisions:` | mutually-exclusive requirements (CAP/latency-bandwidth/strong-vs-eventual/realtime-vs-offline/cost-vs-capability) built without a recorded human tradeoff decision |
| `validate_premise_falsifiable` | `.bagel/expert/problem-framing.yaml` → `premise_fidelity`/`falsifiability:` | unfalsifiable premise (consciousness/qualia/free-will + prove/exists claim) run without reframing to a concrete metric + falsifier |
| `validate_gameable_metric_pairing` | `.bagel/state.yaml` → `evaluation.metrics` | a gameable retrieval headline (hit@1/precision@1/exact-match) used as the sole quality signal without a robustness/ranking pair (MRR/nDCG/MAP/recall@k/held-out) |
| governance budget mode-aware ceiling | `.bagel/telemetry/cycles.yaml` → `budget.governance_token_share` | governance share exceeding the run-mode cap (quick ≤25%, full ≤40%) — per-cycle hard fail, not just a streak warning |
| governance share derived from token_log | `.bagel/telemetry/cycles.yaml` → `token_log` | declared `governance_token_share` inconsistent with the recomputable share from the per-entry `token_log` (governance-category tokens / all tokens) — catches a self-reported lie |
| `validate_production_surface` | source/config/dispatch scan → `.bagel/ledger.yaml` → `human_decisions:` | production-data/credential signals (cloud keys AKIA, non-localhost prod connection strings, prod-host patterns, cloud-SDK usage) without a recorded hard-stop acknowledgment |
| `no_hardcoded_secrets` | generated source/config scan | hardcoded secret/key patterns (AWS AKIA, GitHub PAT, private key blocks, Stripe live keys, Slack tokens) in generated code — fails UNCONDITIONALLY (committed secrets are irreversible leaks, no acknowledgment can clear) |

## Two-tier design

The validators use a **two-tier design**: a structured-declaration path (paraphrase-proof, authoritative) and a signal-substring fallback (catches the common form, evadable by synonym). Always prefer the structured path — declare `requirement_axes` with `{requirement_axis, strength}` from the fixed enum, and `metric_role` from `{gameable_top1, ranking_robustness, held_out_generalization, qualitative, other}`. The substring fallback is a safety net for pre-structured runs only.

Known residual limits, each a platform boundary rather than a skill-design gap:

1. **Substring fallback is evadable by synonym** — but the structured-declaration path is not. `validate_requirement_coherence` checks declared `requirement_axes` against `_AXIS_CONFLICTS` (consistency/availability/partition/latency/offline_window/merge_model/cost/capability) before falling back to signal matching; `validate_gameable_metric_pairing` checks declared `metric_role` before falling back to name matching. Declare structured fields to get the paraphrase-proof guarantee. The structured declaration is **mandatory** once a problem-framing with a stated problem exists (not signal-gated); a `no_contradiction_axes_needed: true` attestation is cross-validated against the stated-problem text and refused if it contradicts a strong-axis signal.
2. **`governance_token_share` is recomputable from `token_log`** — `token_log` is **mandatory** for Build/Iterate cycles that produce a deliverable delta (control-plane-only cycles within Build are exempt); when present, the validator recomputes the governance share from per-entry `{role, tokens, category}` records and fails if the declared share deviates >5% from the derived value. This makes the budget gate falsifiable, not just self-attested. (Residual limit: the token_log entries themselves are agent-recorded; platform-level token accounting would be even stronger.)
3. **The production-data/credential hard-stop (S7) has a mechanical first line** — `scripts/production_surface_check.py` scans source/config/dispatch envelopes (including scripts/deploy/migrations/tests dirs and .env/.envrc/secrets files) for cloud keys (AKIA shapes), non-localhost production connection strings, prod-host patterns, and cloud-SDK usage with region; detected signals without a **structured** hard-stop acknowledgment (`hardstop_type: production_data` + `acknowledged: true` in the ledger) fail the cycle. The human STOP remains the final authority for intent-sensitive judgment. This is a **first line** that catches the naive inline-secrets cheat; env-var indirection (`os.environ.get`) and ORM-config connections are a known residual that the human STOP covers.

Do not present these limits as fully solved. The structured paths, token_log derivation, and credential scanner make the common cheats impossible or falsifiable; the residual risk is a determined adversarial agent fabricating the entire token_log or attestation, which requires platform-level provenance to close.

## The unifying residual (external audit finding, honestly stated)

Every validator is a Python checker the agent is *instructed* to run (loop step 9), reading `.bagel/` YAML the agent authored, cross-checked against other agent-authored YAML. The checkers verify *shape* (fields exist, enums valid, hashes match agent-written hashes) — almost never *ground truth*. A context-degraded agent that wants the run to "succeed" can populate the public schema with plausible prose. Full closure requires **platform-level provenance**: an externally-triggered gate (Claude Code `Stop`/`PostToolUse` hook, or CI on the `.bagel/` commit) that runs the validator independently of the agent; append-only/signed state so post-hoc edits are detectable; and real token/command accounting from the platform, not agent self-report. This is the single most valuable change — one checker the agent cannot choose not to run. Until it exists, the enforcement substrate is *voluntary*, and all guarantees are "hard-to-lazily-fake" not "impossible-to-fake."

### Dependency note (P0-1)

The validator suite's single declared third-party dependency is **PyYAML** (`requirements.txt`). Without it, every sub-check crashes with `ModuleNotFoundError` instead of enforcing gates. The orchestrator (`scripts/bagel_v3_check.py`) detects the missing dependency and prints a clear `FAIL:` with the install command before dispatching any sub-check. Install once per environment: `pip install -r requirements.txt`.
