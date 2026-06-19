# RUN-001 — Real end-to-end live run (leak hunt)

**Date:** 2026-06-19
**Domain:** software (self-verifiable, chosen to distinguish real vs fake progress)
**Product workspace:** `D:\code\bagel-liverun-001` (outside skill repo, own git)
**Mode:** `quick_autonomy`, bounded for a leak-hunt (small budget, low max_iterations) — deliberately compressed so the *loop machinery* is exercised, not an all-night product build. This boundedness is a test choice, recorded, not a degraded run.

## The task (the "north star" a user would give at night)

> Build `linkcheck`: a small, complete CLI tool that scans a directory of markdown / static-site files and reports broken **internal** links and dead **anchors** (`#heading`), with fix suggestions. It should be fast on a few-thousand-file tree, have a low false-positive rate, return CI-friendly exit codes, and ship with tests + a short README. Python, stdlib-first, no network calls.

## User-persona answer key (pre-aligned user — answers the skill's alignment questions)

The operating agent plays the user with these fixed preferences so alignment Q&A is *real* but unattended. If the skill asks something not covered here, the answer is the closest reasonable default below + log it as "alignment gap."

- **North star:** a reliable internal-link/anchor checker for docs sites; value = catch broken links in CI before they ship.
- **Primary users:** docs maintainers / tech writers running it in CI. **Excluded:** end readers, non-technical users.
- **Must-have baseline slices:** (1) crawl md files + parse links/anchors, (2) resolve internal links (relative paths + `#anchors`), (3) report broken ones with file:line, (4) exit non-zero on findings (CI), (5) tests on a known-broken fixture tree.
- **Forbidden / non-goals:** no network/external-URL checking (internal only for v1), no auto-fixing files (suggest only), no config-file system for v1.
- **Constraints:** Python 3.12, stdlib-first (no third-party runtime deps), cross-platform paths, runnable as `python -m linkcheck <dir>`.
- **Autonomy policy:** decide everything reversible alone. Wake only for hard-stop boundaries.
- **Excellence horizon (starting bar, raise from here):** correctness on tricky cases (relative `../`, case sensitivity, anchor slugification, links inside code fences must be ignored), <2% false positives on the fixture set, fast (<1s on 1k files), clean output UX, tests cover happy + error paths.
- **Long-run delegation:** yes, maximum autonomous momentum within the bounded budget for this test.
- **Execution strategy:** balanced_parallel.
- **Alignment depth:** standard.
- **Innovation ambition:** optimize the concept (not breakthrough) — but a differentiated touch (e.g. great fix-suggestions / slug heuristics) is welcome.
- **Stop Contract:** max_iterations=2 (TEST BOUND); budget=strict_cap (small, this session); hard_stops=standard list; within_autonomy=repair/iterate/refactor/add tests; morning_return=working tool + before/after evidence + leak findings; deadline=this session.
- **Briefing format:** Markdown STATUS only.
- **Research mode:** N/A (software).

## What this run is really for

Find where the machinery LEAKS, across the three frontiers:
1. **Ground-truth anchor** — does any validator pass on agent-authored fiction? Is `net_assessment: forward` actually independent?
2. **Iteration engine depth** — does bar-raising / brainstorming produce non-obvious improvements, or just the obvious?
3. **Complexity → outcome** — how much of the run is governance vs product? Does `.bagel/` upkeep compete with the artifact?

Every leak goes in `observer-log.md` with: where, what happened, severity, and a proposed fix.
