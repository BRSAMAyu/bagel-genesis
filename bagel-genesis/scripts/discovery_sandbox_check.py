#!/usr/bin/env python3
"""Explorer (Mode 2, objective: discovery) gate — the two properties that make
divergent autonomous research both SAFE and RIGOROUS:

  1. Zero blast radius (the user's #1 ask). A discovery run may create/modify files
     only under its sandbox (`discovery_contract.sandbox_path`, default
     `.bagel/explore/`) and `.bagel/`. Any change to the user's real project tree is
     a contract violation. This is enforced against the actual changed-file set (git
     porcelain when available, else the platform file-write attestation log), not
     trusted — an Explorer cannot screw up the real project by construction.

  2. Report integrity. Every idea in `.bagel/explore/discovery-report.yaml` must be
     self-validated: a non-empty novelty record (what_is_new), a probe carrying a real
     result, a Judgment Council verdict, and a falsifiable next step. A bare-assertion
     idea cannot enter the deliverable — "creative" must also mean "grounded."

Scope: fires only when `.bagel/constitution.yaml` declares
`research_autonomy.objective: discovery` (or mode autonomous_researcher + a
`discovery_contract`). Inert for every other run.

Honest limit: the blast-radius check sees the changed-file *set*, not intent — it
proves nothing was written outside the sandbox, which is exactly the safety property
the user wants; it does not judge whether the sandboxed work was good (that is the
Judgment Council's job). When neither git nor an attestation log is available it
degrades to a WARN (cannot verify) rather than a false pass.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ALWAYS_ALLOWED = (".bagel/", ".git/", ".gitignore", ".gitattributes", "status.md")


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def discovery_contract(constitution: dict) -> dict | None:
    ra = as_dict(constitution.get("research_autonomy"))
    if not ra:
        return None
    objective = str(ra.get("objective") or "").lower()
    contract = as_dict(ra.get("discovery_contract"))
    if objective == "discovery" or contract:
        return contract or {}
    return None


def _norm(p: str) -> str:
    s = p.replace("\\", "/").strip()
    while s.startswith("./"):
        s = s[2:]
    return s


def _allowed_prefixes(contract: dict) -> tuple[str, ...]:
    sandbox = _norm(str(contract.get("sandbox_path") or ".bagel/explore/"))
    if not sandbox.endswith("/"):
        sandbox += "/"
    return (sandbox,) + ALWAYS_ALLOWED


def offending_paths(changed: list[str], allowed: tuple[str, ...]) -> list[str]:
    """Pure classifier: which changed paths fall outside the allowed prefixes."""
    out = []
    for raw in changed:
        rel = _norm(raw)
        if not rel:
            continue
        if any(rel == a.rstrip("/") or rel.startswith(a) for a in allowed):
            continue
        out.append(rel)
    return out


def _git_changed(root: Path) -> list[str] | None:
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
        )
    except Exception:
        return None
    if res.returncode != 0:
        return None
    paths: list[str] = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        body = line[3:] if len(line) > 3 else line.strip()
        if " -> " in body:  # rename: old -> new, take the new path
            body = body.split(" -> ", 1)[1]
        paths.append(body.strip().strip('"'))
    return paths


def _attested_writes(root: Path) -> list[str] | None:
    """Fallback: distinct file_path values from platform file-write attestations."""
    adir = root / ".bagel/attestations"
    if not adir.exists():
        return None
    paths: set[str] = set()
    found = False
    for f in adir.rglob("*"):
        if not f.is_file():
            continue
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for rec in as_list(data if isinstance(data, list) else [data]):
            rec = as_dict(rec)
            if str(rec.get("tool") or "").lower() != "write":
                continue
            fp = as_dict(rec.get("tool_input")).get("file_path")
            if fp:
                found = True
                paths.add(str(fp))
    return sorted(paths) if found else None


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    contract = discovery_contract(constitution)
    if contract is None:
        return errors, warnings  # not a discovery run

    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    run_status = str(state.get("run_status") or state.get("status") or "")
    allowed = _allowed_prefixes(contract)

    # ---- 1. Zero blast radius ----------------------------------------------
    changed = _git_changed(root)
    source = "git"
    if changed is None:
        changed = _attested_writes(root)
        source = "attestation log"
    if changed is None:
        warnings.append(
            "discovery_sandbox: cannot verify blast radius — neither git nor a "
            "file-write attestation log is available. The sandbox-only contract is "
            "UNVERIFIED for this run (configure BAGEL_ATTEST_KEY or run under git)."
        )
    else:
        offenders = offending_paths(changed, allowed)
        if offenders:
            shown = ", ".join(offenders[:8]) + (" …" if len(offenders) > 8 else "")
            errors.append(
                f"discovery_sandbox: blast-radius violation ({source}) — a discovery "
                f"run modified files outside the sandbox ({allowed[0]}) and .bagel/: "
                f"{shown}. Discovery must not touch the user's real project; move this "
                "work into the sandbox."
            )

    # ---- 2. Report integrity ------------------------------------------------
    report_doc = as_dict(load_yaml(root / ".bagel/explore/discovery-report.yaml", {}))
    report = as_dict(report_doc.get("discovery_report")) or report_doc
    ideas = [as_dict(i) for i in as_list(report.get("ideas"))]

    if not ideas:
        if run_status == "complete":
            errors.append(
                "discovery_sandbox: discovery run is complete but "
                ".bagel/explore/discovery-report.yaml has no ideas — the deliverable "
                "(vetted ideas) was never produced"
            )
        return errors, warnings  # in-progress: nothing to integrity-check yet

    for idea in ideas:
        iid = idea.get("id") or idea.get("title") or "?"
        nov = as_dict(idea.get("novelty_record"))
        if not str(nov.get("what_is_new") or "").strip():
            errors.append(
                f"discovery_sandbox: idea {iid!r} has no novelty_record.what_is_new — "
                "an idea that cannot state its delta vs known work cannot be reported"
            )
        probe = as_dict(idea.get("probe"))
        if not str(probe.get("result") or "").strip():
            errors.append(
                f"discovery_sandbox: idea {iid!r} has no probe.result — a reported idea "
                "must be self-validated by the cheapest experiment that updates belief"
            )
        if not str(idea.get("council_verdict") or "").strip():
            errors.append(
                f"discovery_sandbox: idea {iid!r} has no council_verdict — survivors are "
                "selected by the Judgment Council, not asserted"
            )
        if not str(idea.get("falsifiable_next") or "").strip():
            errors.append(
                f"discovery_sandbox: idea {iid!r} has no falsifiable_next — a vetted idea "
                "must name the next real experiment that would pursue it"
            )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    errors, warnings = validate(Path(args.root).resolve())
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL discovery-sandbox check passed.")
    return 0


def _GOOD_IDEA():
    return {
        "id": "DISC-001",
        "novelty_record": {"what_is_new": "a per-step attention-entropy probe",
                           "known_work": ["generic attention rollout"]},
        "probe": {"command": "python explore/probe.py", "result": "entropy spikes at step 7"},
        "council_verdict": "passed",
        "falsifiable_next": "run the probe across 50 long-horizon traces",
    }


def _self_test() -> int:
    import copy

    # Pure classifier tests (blast radius).
    allowed = _allowed_prefixes({"sandbox_path": ".bagel/explore/"})
    classifier_cases = [
        ("sandbox file allowed", [".bagel/explore/probe.py"], []),
        ("bagel control plane allowed", [".bagel/state.yaml"], []),
        ("real project file offends", ["src/model.py"], ["src/model.py"]),
        ("mixed", [".bagel/explore/a.py", "app/main.ts"], ["app/main.ts"]),
        ("windows sep + dotslash", [".\\.bagel\\explore\\x"], []),
    ]
    passed = 0
    total = 0
    for name, changed, expect in classifier_cases:
        total += 1
        got = offending_paths(changed, allowed)
        ok = got == [_norm(p) for p in expect]
        print(f"{'PASS' if ok else 'FAIL'}  [classify] {name}" + ("" if ok else f"  (got {got})"))
        passed += int(ok)

    # Report-integrity tests (run validate against temp dirs, git unavailable -> WARN only).
    import tempfile

    def run(report, complete=False):
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / ".bagel/explore").mkdir(parents=True)
        (root / ".bagel/constitution.yaml").write_text(yaml.safe_dump(
            {"research_autonomy": {"mode": "autonomous_researcher", "objective": "discovery",
                                   "discovery_contract": {"sandbox_path": ".bagel/explore/"}}}),
            encoding="utf-8")
        (root / ".bagel/state.yaml").write_text(yaml.safe_dump(
            {"run_status": "complete" if complete else "iterate"}), encoding="utf-8")
        if report is not None:
            (root / ".bagel/explore/discovery-report.yaml").write_text(
                yaml.safe_dump(report), encoding="utf-8")
        return validate(root)

    integrity_cases = []
    integrity_cases.append(("good idea -> no errors", {"discovery_report": {"ideas": [_GOOD_IDEA()]}}, True))

    bad = copy.deepcopy(_GOOD_IDEA()); bad["novelty_record"]["what_is_new"] = ""
    integrity_cases.append(("missing what_is_new -> error", {"discovery_report": {"ideas": [bad]}}, False))

    bad = copy.deepcopy(_GOOD_IDEA()); bad["probe"]["result"] = ""
    integrity_cases.append(("missing probe result -> error", {"discovery_report": {"ideas": [bad]}}, False))

    bad = copy.deepcopy(_GOOD_IDEA()); del bad["falsifiable_next"]
    integrity_cases.append(("missing falsifiable_next -> error", {"discovery_report": {"ideas": [bad]}}, False))

    for name, report, expect_clean in integrity_cases:
        total += 1
        errors, _ = run(report)
        ok = (len(errors) == 0) == expect_clean
        print(f"{'PASS' if ok else 'FAIL'}  [integrity] {name}" + ("" if ok else f"  (errors={errors})"))
        passed += int(ok)

    # Complete + no report -> error
    total += 1
    errors, _ = run(None, complete=True)
    ok = len(errors) == 1
    print(f"{'PASS' if ok else 'FAIL'}  [integrity] complete w/o report -> error" + ("" if ok else f"  (errors={errors})"))
    passed += int(ok)

    print(f"{passed}/{total} self-test cases passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
