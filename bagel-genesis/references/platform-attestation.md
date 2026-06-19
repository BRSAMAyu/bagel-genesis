# Platform Attestation Layer (V5)

This closes the structural residual disclosed in
[`enforcement-honesty.md`](enforcement-honesty.md#residual-limit): every V4
validator reads agent-authored YAML and verifies *shape*, almost never
*ground truth*. The attestation layer adds a third tier of evidence — bytes
a real command produced under the harness, signed by a key the agent cannot
read — so a research claim's headline number must trace to a genuinely
executed command, not to an agent-authored file.

## The three tiers

| Tier | Who writes it | Can the agent forge it? | Examples |
|---|---|---|---|
| Mechanical execution | validator scripts | No | secret scan, falsifier regex |
| Agent attestation | the agent (YAML) | Yes (shape-only) | plan-hash, authority_ref, reproducibility_status |
| **Platform attestation (V5)** | **harness hook process** | **Partially** — see threat model below | command really ran (vs not), plan written before runs, append-only dir |

When platform attestation is configured, validators upgrade tier-2 gates to
tier-3 wherever a binding exists, and report the run as **VERIFIED**. When it
is not configured, the skill still works but reports **UNATTESTED** and every
gate falls back to shape-only (the pre-V5 behavior, honestly disclosed).

## Setup (Claude Code)

1. **Generate a signing key in your shell** (not in the repo, not in any file
   the agent can read):

   ```sh
   # ~/.zshrc  (or ~/.bashrc)
   export BAGEL_ATTEST_KEY="$(openssl rand -hex 32)"
   ```

   Restart your shell or `source ~/.zshrc`. Verify: `echo $BAGEL_ATTEST_KEY`.

   The key lives only in your interactive shell environment. The hook process
   (spawned by the harness, not the agent) inherits it; the agent's own Bash
   subprocesses do not, because the harness exports a filtered environment to
   tool calls.

2. **Install the hook.** Copy `.claude/settings.json` from this skill (or merge
   its `hooks` block into your project's `.claude/settings.json`). Replace
   `SKILL_PATH` with the absolute path to this skill directory, e.g.
   `/Users/you/.claude/skills/bagel-genesis`.

3. **Run BAGEL as usual.** The hook silently attests every Bash command. The
   suite's `attestation_check.py` (first in the run order) reports the state:
   - `VERIFIED (N attested command outputs)` — tier-3 active
   - `UNATTESTED` — key not set or no commands attested yet; tier-3 inactive
   - `TAMPERED` — signature/chain broken; suite fails loudly

## What changes for research runs

Under attested mode, `evidence_replay_check.py` enforces one additional rule
for `metric_recompute` evidence: `extracts_from` must resolve to a
platform-attested Bash command's stdout (matching `stdout_sha256`), and that
command must look like a substantive training/eval entry-point (not `echo`/
`cat`/`print`). This means a headline metric value must come from bytes a
real command produced — you cannot fabricate it by writing a YAML file.

If the attested command was not a compute entry-point, or no attestation
matches the artifact hash, the gate fails with a clear message.

## Threat model & honest limits

### What the layer genuinely closes (action-layer, key-independent)

These gates work **regardless of whether the agent can read the key**, because
they intercept actions at the tool-call boundary, not by cryptographic secrecy:

- **`.bagel/attestations/` append-only guard** (`attest_fileop.py`
  PreToolUse on Write/Edit/MultiEdit): the agent cannot use the Write/Edit
  tools to mutate the attestation directory. This is enforced by the harness
  refusing the tool call (exit 2 block) before it executes.
- **Emergency-stop hard interception** (`attest_fileop.py` PreToolUse on Bash):
  when `.bagel/STOP_REQUESTED` exists, the harness blocks the next Bash call.
  This converts the V4 advisory stop into a next-action kill switch.
- **External validator trigger** (`attest_stop.py` Stop hook): the suite runs
  at turn end independent of the agent choosing to run it.
- **Control-plane-first gate** (`attest_fileop.py` PreToolUse on
  Write/Edit/MultiEdit, **opt-in** via `BAGEL_REQUIRE_CONTROL_PLANE=1`): while
  enabled and `.bagel/constitution.yaml` does not yet exist, the harness blocks
  any product/source write (only bootstrap paths — `.bagel/`, `status.md`,
  `.git*` — are allowed) and returns an instruction to create the control plane
  first. This is the one forcing function for *engagement itself*: it converts
  "the agent ignored the skill and just wrote code" from a silent pass into a
  blocked action, at the tool boundary, regardless of whether the agent read
  SKILL.md. Off by default so it never surprises a non-BAGEL repo; a no-op once
  the constitution exists. It does not force *good* engagement (the agent can
  write a minimal constitution to unblock), but it guarantees the Align artifact
  exists before any product code, which the rest of the suite then has something
  to check against. See `references/gate-predicates.md` `control_plane_first`.

### What the layer does NOT close — the key-isolation limit (structural)

**The signing key `BAGEL_ATTEST_KEY` is readable by the agent.** An earlier
version of this document claimed the harness exports a filtered environment to
tool subprocesses. **That claim is false.** Claude Code's Bash tool executes
in the full Claude Code process environment; the agent's Bash subprocesses
inherit `BAGEL_ATTEST_KEY` along with `PATH`/`HOME`/etc. Verified empirically:
`printenv BAGEL_ATTEST_KEY` from an agent Bash call returns the key, and a
forged attestation produced with `attestation_lib.write_record()` passes
signature verification as VERIFIED, indistinguishable from a real one.

Consequence: **the cryptographic signature does not, on its own, bind a claim
to bytes a real command produced.** An informed agent (including any subagent
that has read this file) can forge a complete, valid-looking attestation chain
in ~1 minute. The signature layer therefore raises the bar only against an
*uninformed* or *lazy* agent that doesn't realize it can read the key.

This is a structural limit of the skill-in-a-harness model, not a bug to be
patched in this layer: **any value the hook process can read, the agent's Bash
subprocess can also read**, because both run under the same Claude Code process
environment. Closing it fully requires a secret the hook can access but the
agent cannot — which is not achievable from inside the agent's own tool
surface. The real closure is external: run the validator (and the signing) in
a process the agent does not control — e.g. CI on the `.bagel/` commit, or a
sidecar auditor with its own credentials. That is out of scope for a skill.

### Subagent dispatch binding (true_subagents proof)

`scripts/attest_subagent.py` (PostToolUse on the `Task` tool) closes a concrete
shape-only leak: a hand-written `.bagel/evidence/runtime/subagent-proof.yaml`
with **zero real dispatch behind it** used to pass `runtime_proof_check.py`,
byte-indistinguishable from a genuine proof. Now:

- The detector defaults `true_subagents.observed` to `unknown` (CLI presence is
  not observation). It is flipped to `true` only by the hook, on a real dispatch.
- The hook writes a signed `tool: Task` attestation whose `agent_id` comes from
  the platform `tool_response`, and refreshes the proof's `verifier_agent_id` +
  `attestation_ref` from it — the hook process writes these, not the agent.
- When the key is set, `runtime_proof_check.py` requires the `true_subagents`
  proof to bind to a real signed Task attestation (by `attestation_ref` or
  `verifier_agent_id`). A forged proof with no matching attestation **fails**.
- When the key is absent, it degrades to the pre-existing shape-only check
  (honest UNATTESTED fallback — unchanged behavior).

Honest limit: identical to the rest of this layer — an *informed* agent that
reads the key can still mint a forged Task attestation. This binds the proof to
a real dispatch under key isolation and closes the uninformed/lazy path; full
closure is external (CI). The Task `tool_response` shape also varies by harness
version, so agent-id extraction is best-effort (the `attestation_ref` binding
does not depend on it).

### Other honest limits

- The layer proves "command X ran and produced bytes Y." It does NOT prove
  "command X was a faithful implementation of the preregistered protocol." A
  malicious agent can still run a real but wrong command (e.g. `python cheat.py`
  that hardcodes a number, or an empty-shell plan written early then filled
  after results). The non-triviality heuristic raises cost but is not proof.
- PostToolUse `tool_response.stdout` may be truncated by the harness for very
  large outputs (MB-scale training logs); the attested stdout hash is over the
  (possibly truncated) bytes the harness captured. For large logs, prefer
  writing to a file in the command and attesting the file path.
- Other platforms (Codex, Cursor) without PostToolUse/PreToolUse hooks cannot
  run this tier. The skill detects this and degrades to UNATTESTED rather than
  failing.

## Files

| Path | Role |
|---|---|
| `scripts/attestation_lib.py` | signing, chain, read/verify (shared by hook + validators) |
| `scripts/attest_bash.py` | PostToolUse hook for Bash (writes attestations) |
| `scripts/attest_fileop.py` | PreToolUse guards (attestation append-only, emergency-stop, opt-in control-plane-first) + PostToolUse file-write attestation |
| `scripts/attest_subagent.py` | PostToolUse hook for Task (binds true_subagents proof to a real signed dispatch) |
| `scripts/attestation_check.py` | suite validator (first gate; reports VERIFIED/UNATTESTED/TAMPERED) |
| `.claude/settings.json` | hook installation template |
| `scripts/evidence_replay_check.py` | gains `--attested` mode binding extracts_from to attestations |
