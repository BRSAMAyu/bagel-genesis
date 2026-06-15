# BAGEL Genesis

> Turn a vague vision or an existing partially-built project into an excellent finished deliverable through **deep upfront alignment** followed by **sustained autonomous iteration**.

BAGEL Genesis is a **skill-level operating protocol** for agent systems (Claude Code, Codex, and similar). It is not a monolithic prompt. It performs deeper-than-native planning alignment, then runs an autonomous loop that keeps improving until the deliverable reaches an explicitly defined excellence horizon.

## Why this exists

Native agent "plan modes" do shallow alignment (a few quick questions) and then stop frequently for approval. If you go to sleep after aligning a vision, you want to wake up to either finished excellent work or clear evidence the agent ran the whole night and hit a real wall — **not silence, not "waiting for approval," not trivial polish dressed as progress.**

BAGEL is built around that contract:

- **Deep alignment first** — surface hidden assumptions and unresolved decisions *before* autonomous execution, so the agent can run for many hours without constant intervention.
- **Long-run autonomy by default** — after delegation, the agent continues through friction (repairs, missing tools, failed attempts, alternative paths) instead of stopping. It stops only for genuine hard-stop boundaries: irreversible/non-recoverable destructive action, serious security/privacy/legal/financial/production-data risk, credentials or paid resources, core identity changes, or an explicit user-forbidden boundary.
- **Objective progress, not self-assessment** — every cycle writes a quantified progress delta (`forward / lateral / backward`); three consecutive `lateral` cycles force a strategy switch rather than idle looping.
- **Strict loading discipline** — a single authoritative Loading Matrix says exactly when each reference file must be read strictly and when it must not be loaded at all. File count is not bloat; unstructured loading is.

## Three control-plane tiers

| Mode | When | State files |
|---|---|---|
| `quick_autonomy` (default) | existing projects, bounded modules, clear optimization/research goals | 5 core files: `state.yaml`, `constitution.yaml`, `context.yaml`, `ledger.yaml`, `STATUS.md` |
| `full_genesis` | blank-slate products, multi-day builds, broad takeover | full detailed artifact set, expanded lazily per stage |
| `parallel_advanced` | multiple write agents or worktrees actually active | adds git locks, merge queue, agent registry |

## Workflow

```text
Align: ask enough to make the vision executable.
Build: slice -> implement -> verify -> record progress delta -> next slice.
Polish: critique -> improve -> verify -> record progress delta -> next highest-EV pass.
```

## Structure

```
SKILL.md                  # entry point + Core Philosophy + Tie-Breaker + Loading Matrix
references/               # 30 protocol references, loaded strictly by trigger (see Loading Matrix)
agents/                   # 13 role prompts (orchestrator, implementer, reviewers, court, red-team, ...)
scripts/
  skill_lint.py           # consistency lint
  detect_runtime_capabilities.py  # probe platform capabilities before a long run
evals/evals.json          # 28 evals covering alignment, autonomy, recovery, platform binding
```

## Using it

Install as a skill in your agent platform (Claude Code / Codex), then invoke it with a vague vision or an existing project you want polished. The skill will run deep alignment, then enter autonomous build/polish loops.

See `SKILL.md` for the full operating protocol and the authoritative Loading Matrix.

## Status

This skill is under active development. It has been through internal-consistency auditing (P0 contradictions resolved, quick/full propagation verified) but **has not yet been validated by long unattended runs in production**. Treat the autonomy claims as design intent until you have run it yourself.

## License

MIT
