#!/usr/bin/env python3
"""Finding/claim verification gate — a review/research finding may only count
toward net_assessment if its demonstrating input was actually EXECUTED and
reproduced the claimed defect.

Why (RUN-002 finding 7): a single independent reviewer is rigorous but not
ground truth — in the live linkcheck run the reviewer emitted a confident P0
("bare `#` must be reported broken") that was simply WRONG (the spec skips
`#`-only links; the tool was correct), alongside a real P1 (code-fence links
over-reported) that reproduced. Shape checks can prove "a reviewer ran"; they
cannot prove "its findings are correct." The only thing that separated the two
was RUNNING the demonstrating input. This gate makes that mechanical.

Schema — `.bagel/reviews/<REV-id>.yaml`:

    review:
      review_id: REV-047
      reviewer_agent_id: <independent reviewer id>
      net_assessment: forward | lateral | backward
      findings:
        - finding_id: F1
          sev: P0 | P1 | P2 | INFO
          title: "code-fence links over-reported"
          counts_toward_net_assessment: true        # only confirmed defects
          reproduction:
            command: "python linkcheck.py /tmp/fence"
            expectation: "broken link -> nope.md"    # substring proving the defect
            result: reproduced | not_reproduced
            evidence_ref: ".bagel/attestations/outputs/<sha>.out"  # attested stdout

Rules:
  1. A finding with counts_toward_net_assessment=true AND sev in {P0,P1} MUST
     carry a reproduction block whose result == "reproduced".
  2. A finding whose reproduction.result == "not_reproduced" MUST NOT have
     counts_toward_net_assessment=true (the false-P0 case is auto-excluded).
  3. net_assessment consistency: if any P0/P1 counts, net_assessment must be
     "backward" (a confirmed new P0/P1 is a regression vs the candidate); a
     review may only be "forward" when zero P0/P1 count toward it.
  4. ATTESTED MODE (BAGEL_ATTEST_KEY set + attestations present): a "reproduced"
     finding's reproduction must bind to a REAL attested Bash command — the
     attested command output must contain `expectation`. A reproduction claim
     with no matching attested command FAILS. Without a key → shape-only (the
     result field is trusted), honest UNATTESTED degradation, behavior unchanged.

This is the same anchor as the runtime-proof binding: a load-bearing judgment is
tied to bytes a real command produced, forge-resistant under key isolation, with
the same honestly-stated residual (an informed agent that reads the key can mint
a forged attestation; full closure stays external/CI).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _attested_outputs(root: Path) -> tuple[dict, list[str], bool]:
    """When BAGEL_ATTEST_KEY is set, return {command: attestation} for verified
    Bash outputs, plus chain errors, plus active=True. Off (active=False) when
    no key — callers keep shape-only behavior."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import attestation_lib as al
    except Exception:
        return {}, [], False
    if not al.has_key():
        return {}, [], False
    chain_errors, verified = al.validate_chain(root, al.get_key())
    return al.index_outputs(verified), chain_errors, True


def _attested_stdout_contains(root: Path, index: dict, command: str, needle: str) -> bool:
    """True if an attested command (matching `command`) produced stdout that
    contains `needle`. Reads the attested stdout file by its recorded path."""
    att = index.get(command)
    if not att:
        # Fall back to a loose match: any attested command whose recorded
        # command string contains the reproduction command (covers cwd prefixes).
        for cmd, a in index.items():
            if command and command in cmd:
                att = a
                break
    if not att:
        return False
    # The stdout bytes were captured to .bagel/attestations/outputs/<sha>.out
    sha = str(att.get("stdout_sha256") or "")
    out_path = root / ".bagel" / "attestations" / "outputs" / f"{sha}.out"
    if not out_path.exists():
        return False
    try:
        text = out_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return needle in text


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    reviews_dir = root / ".bagel" / "reviews"
    if not reviews_dir.exists():
        return errors, warnings

    att_index, chain_errors, attested = _attested_outputs(root)
    if attested and chain_errors:
        errors.extend(f"attestation chain: {e}" for e in chain_errors)

    for path in sorted(reviews_dir.glob("*.yaml")):
        doc = as_dict(load_yaml(path, {}))
        review = as_dict(doc.get("review") or doc)
        rid = str(review.get("review_id") or path.stem)
        findings = as_list(review.get("findings"))
        net = str(review.get("net_assessment") or "")
        counted_p0p1 = 0

        for f in findings:
            f = as_dict(f)
            fid = str(f.get("finding_id") or "?")
            sev = str(f.get("sev") or "").upper()
            counts = bool(f.get("counts_toward_net_assessment"))
            repro = as_dict(f.get("reproduction"))
            result = str(repro.get("result") or "")

            # Rule 2: a non-reproduced finding cannot count.
            if result == "not_reproduced" and counts:
                errors.append(
                    f"{rid}/{fid}: reproduction.result=not_reproduced but "
                    "counts_toward_net_assessment=true — a finding that does not "
                    "reproduce must NOT count (the false-P0 case)"
                )

            if counts and sev in {"P0", "P1"}:
                counted_p0p1 += 1
                # Rule 1: counted P0/P1 needs a reproduced demonstrating input.
                if not repro:
                    errors.append(
                        f"{rid}/{fid}: counted {sev} has no reproduction block — "
                        "a counted defect must carry an executable demonstrating input"
                    )
                    continue
                if result != "reproduced":
                    errors.append(
                        f"{rid}/{fid}: counted {sev} reproduction.result={result!r} "
                        "(must be 'reproduced')"
                    )
                    continue
                command = str(repro.get("command") or "")
                expectation = str(repro.get("expectation") or "")
                if not command or not expectation:
                    errors.append(
                        f"{rid}/{fid}: reproduction needs both `command` and `expectation`"
                    )
                    continue
                # Rule 4: attested-mode binding to a real executed command.
                if attested:
                    if not _attested_stdout_contains(root, att_index, command, expectation):
                        errors.append(
                            f"{rid}/{fid}: attested mode — no attested command output "
                            f"matches command {command!r} containing expectation "
                            f"{expectation!r}; reproduction is not backed by a real run"
                        )

        # Rule 3: net_assessment consistency.
        if net == "forward" and counted_p0p1 > 0:
            errors.append(
                f"{rid}: net_assessment=forward but {counted_p0p1} confirmed P0/P1 "
                "count toward it — a confirmed new P0/P1 cannot be 'forward'"
            )
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--self-test", action="store_true", help="run built-in fixtures")
    # Accepted (no-op) so the suite can append it uniformly; this gate has no
    # warning tier — every emission is a hard failure.
    parser.add_argument("--strict-warnings", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    errors, warnings = validate(Path(args.root).resolve())
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors:
        return 1
    print("BAGEL finding-verification check passed.")
    return 0


def _self_test() -> int:
    """Self-contained fixtures proving both the pass and the fail paths, modeled
    on the real RUN-002 result (false bare-`#` P0 + real code-fence P1)."""
    import tempfile

    cases = [
        # (name, review_doc, expect_pass)
        (
            "real-P1-reproduced-counts -> backward (OK)",
            {"review": {"review_id": "REV-OK", "net_assessment": "backward", "findings": [
                {"finding_id": "F-fence", "sev": "P1", "counts_toward_net_assessment": True,
                 "reproduction": {"command": "python linkcheck.py /tmp/fence",
                                  "expectation": "broken link -> nope.md", "result": "reproduced"}},
            ]}},
            True,
        ),
        (
            "false-P0 not_reproduced but counted -> FAIL",
            {"review": {"review_id": "REV-BAD1", "net_assessment": "backward", "findings": [
                {"finding_id": "F-bare", "sev": "P0", "counts_toward_net_assessment": True,
                 "reproduction": {"command": "python linkcheck.py /tmp/bare",
                                  "expectation": "broken anchor -> #", "result": "not_reproduced"}},
            ]}},
            False,
        ),
        (
            "counted P1 with no reproduction block -> FAIL",
            {"review": {"review_id": "REV-BAD2", "net_assessment": "backward", "findings": [
                {"finding_id": "F-x", "sev": "P1", "counts_toward_net_assessment": True},
            ]}},
            False,
        ),
        (
            "forward but a P0 counts -> FAIL (inconsistent)",
            {"review": {"review_id": "REV-BAD3", "net_assessment": "forward", "findings": [
                {"finding_id": "F-y", "sev": "P0", "counts_toward_net_assessment": True,
                 "reproduction": {"command": "c", "expectation": "e", "result": "reproduced"}},
            ]}},
            False,
        ),
        (
            "false-P0 correctly NOT counted -> OK",
            {"review": {"review_id": "REV-OK2", "net_assessment": "backward", "findings": [
                {"finding_id": "F-bare", "sev": "P0", "counts_toward_net_assessment": False,
                 "reproduction": {"command": "c", "expectation": "e", "result": "not_reproduced"}},
                {"finding_id": "F-fence", "sev": "P1", "counts_toward_net_assessment": True,
                 "reproduction": {"command": "python linkcheck.py /tmp/fence",
                                  "expectation": "broken link -> nope.md", "result": "reproduced"}},
            ]}},
            True,
        ),
    ]
    passed = 0
    for name, doc, expect_pass in cases:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rdir = root / ".bagel" / "reviews"
            rdir.mkdir(parents=True)
            (rdir / f"{doc['review']['review_id']}.yaml").write_text(
                yaml.safe_dump(doc), encoding="utf-8")
            errors, _ = validate(root)
            ok = (len(errors) == 0) == expect_pass
            print(f"{'PASS' if ok else 'FAIL'}  {name}"
                  + ("" if ok else f"  (errors={errors})"))
            passed += int(ok)
    print(f"{passed}/{len(cases)} self-test cases passed.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
