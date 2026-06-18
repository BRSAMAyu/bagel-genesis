# CI Research Auditor — the one layer the agent cannot reach

This is the **structural closure** of the residual that `enforcement-honesty.md`
discloses and that the V5 in-skill attestation layer could not close: every
in-skill check (mechanical, agent-attested, even the signed-hook attestation)
ultimately runs inside the agent's reach — the agent's Bash subprocesses inherit
the same Claude Code process environment, so any secret a hook can read, the
agent can read too (`printenv BAGEL_ATTEST_KEY` returns the key; a forged
attestation verifies as VALID).

The CI auditor breaks that deadlock because it runs in a process **the agent
does not control**: GitHub Actions, with a private-key secret
(`BAGEL_AUDIT_PRIVATE_KEY_PEM`) that exists only on the CI runner — never in the repo,
never in the agent's environment. The agent cannot `printenv` a value that was
never present in any process it can reach.

## What it closes (each was open at the skill layer)

| Residual | Skill-layer status | CI closure |
|---|---|---|
| HARKing (plan written after results) | timestamps agent-authored, forgeable | **strict git DAG ancestry**: the commits introducing `experiment-plan.yaml` and `preregistration.yaml` must strictly predate the first result artifact commit. Same-commit plan+result fails. |
| Plan edited after preregistration | prereg hash is agent-authored YAML | **immutable preregistration record**: `.bagel/research/preregistration.yaml` pins plan path/hash/commit. `state.yaml` hashes are not accepted by CI. |
| Fabricated metric value | extractor reads or prints agent-written value | **hash-pinned recompute from committed bytes + command pins**: CI requires `extracts_from`, `extracts_from_sha256`, `command_ref`, and a preregistered `command_pins[]` sha. Trivial `echo/cat/printf/python -c` producers fail. |
| Fabricated p-value (real metric, fake significance) | p_value is a YAML literal, never recomputed | **per-seed provenance**: seed values must come from distinct `run_ref` metric evidence with seed binding; YAML-only per-seed literals, duplicate run refs, duplicate artifacts, and zero-variance significant claims fail. |
| Verdict forgery | n/a | verdict signed with a CI-only private key; local verifier checks the public key against an out-of-band `BAGEL_AUDIT_PUBLIC_KEY_SHA256` trust anchor. The repo public key alone is not a trust root. |

## Setup

1. **Generate an asymmetric keypair locally** (private key never in the repo):
   ```sh
   openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out ci-audit-private.pem
   openssl rsa -in ci-audit-private.pem -pubout -out .bagel/audit/ci-audit-public.pem
   ```
2. **Add as a GitHub Actions secret**: repo → Settings → Secrets and variables →
   Actions → New repository secret → name `BAGEL_AUDIT_PRIVATE_KEY_PEM`, paste
   the full private PEM.
3. **Workflow permissions**: Settings → Actions → General → Workflow permissions
   → "Read and write" (so the audit-bot can commit the verdict).
4. **Required branch protection**: forbid force-push, require the BAGEL audit
   workflow/check before merging, and protect workflow-file changes from
   unreviewed agent edits. Without this, CI verdicts are not a structural claim.
5. **Record protection status** in `.bagel/audit/ci-protection.yaml`. Local
   `ci_readiness_check.py` reports `NOT_CI_PROTECTED` until this is attested.
6. **Set reviewer trust anchor** before local verification:
   `export BAGEL_AUDIT_PUBLIC_KEY_SHA256=$(sha256sum .bagel/audit/ci-audit-public.pem | awk '{print $1}')`
   from a trusted checkout or reviewer secret store. Without this, local
   `audit_verifier.py` refuses to upgrade claims.

## How it flows

```
agent commits .bagel/research/* → push to GitHub
   → CI checks out full history
   → ci_auditor.py:
       1. git DAG: plan/prereg commits strictly before result commit?
       2. plan sha256 at HEAD == frozen preregistration.yaml?
       3. for each headline claim: hash-pinned extractor invokes preregistered command_ref
       4. if per-seed values: recompute from distinct seed-bound run_ref evidence
       → writes .bagel/audit/VERDICT-<sha>.yaml (signed with CI key)
   → CI commits + pushes the verdict
local suite:
   → audit_verifier.py reads VERDICT-<HEAD-short>.yaml
   → PASS_SIGNED → headline claims upgraded to "CI-verified"
   → FAIL_SIGNED → suite FAILs (research integrity blocked)
   → NOT_AUDITED → claims stay shape-only, clearly labeled
```

## Honest limits (this layer's residuals)

- **Faithful implementation**: CI proves the committed `train.py` produced the
  committed artifact bytes; it does NOT prove `train.py` faithfully implements
  the preregistered protocol. V4.2 command pins prevent post-hoc script swapping,
  but a malicious pinned script can still implement the wrong protocol. Required
  human code review of experiment entrypoints remains the final backstop.
- **Recompute scope**: metric_extractor + paired-t recompute cover the two most
  common fabrication vectors (fake number, fake significance). They do not cover
  every statistical subtlety (CIs, multiple-comparison family sizing beyond
  flagging order-of-magnitude p mismatch). Add checks as needed.
- **Commit-then-edit race**: if the agent pushes a clean commit, CI audits it,
  then the agent amends and force-pushes before CI finishes, the verdict could
  be stale. Required branch protection (no force-push) closes this.
- **CI private-key compromise**: if `BAGEL_AUDIT_PRIVATE_KEY_PEM` leaks,
  verdicts can be forged. Rotate the secret; audit-bot commits are themselves
  git-history-protected.
- **Repo public-key replacement**: the committed public key is not a trust root.
  Local verification requires out-of-band `BAGEL_AUDIT_PUBLIC_KEY_SHA256`.
- **No CI configured**: the skill works fully without this layer — every gate
  falls back to shape-only and `audit_verifier.py` reports NOT_AUDITED. You lose
  the ground-truth upgrade but nothing breaks.

## Files

| Path | Role |
|---|---|
| `scripts/ci_auditor.py` | runs in CI; strict git DAG + prereg pin + metric + statistic recompute; signs verdict |
| `scripts/audit_verifier.py` | local suite gate; verifies public-key-signed verdict for current HEAD |
| `scripts/ci_readiness_check.py` | reports whether branch/workflow/secret protection has been attested |
| `.github/workflows/bagel-audit.yml` | CI trigger; commits verdict back |
| this file | threat model + setup |
