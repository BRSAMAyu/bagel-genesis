#!/usr/bin/env python3
"""Validate replayable BAGEL evidence records and file hashes."""

from __future__ import annotations

import argparse
import hashlib
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_RUNNABLE = {"evidence_id", "command", "cwd", "git_ref", "started_at", "finished_at", "exit_code", "stdout_path", "stderr_path", "stdout_sha256", "stderr_sha256", "env_digest", "replay_policy"}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_bytes(value: bytes) -> bytes:
    return b"\n".join(line.rstrip() for line in value.replace(b"\r\n", b"\n").split(b"\n")).strip()


def extract_number(text: str, metric_name: str | None = None) -> float | None:
    if metric_name:
        pattern = re.compile(rf"{re.escape(metric_name)}\s*[:=, ]\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)")
        m = pattern.search(text)
        if m:
            return float(m.group(1))
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)
    return float(nums[-1]) if nums else None


def validate_metric_recompute(root: Path, path: Path, record: dict[str, Any], policy: dict[str, Any], errors: list[str], attested_outputs: dict[str, dict[str, Any]] | None = None) -> None:
    evidence_id = record.get("evidence_id", "<unknown>")
    extractor = record.get("metric_extractor") or policy.get("metric_extractor")
    metric_name = record.get("metric_name") or policy.get("metric_name")
    declared = record.get("declared_value", policy.get("declared_value"))
    tolerance = record.get("recompute_tolerance", policy.get("recompute_tolerance"))
    if not extractor:
        errors.append(f"{path}: metric_recompute evidence {evidence_id} requires metric_extractor")
        return
    if not isinstance(declared, (int, float)):
        errors.append(f"{path}: metric_recompute evidence {evidence_id} requires numeric declared_value")
        return
    if not isinstance(tolerance, (int, float)):
        errors.append(f"{path}: metric_recompute evidence {evidence_id} requires numeric recompute_tolerance")
        return
    # Anti-fabrication: a bare `echo 0.847` or `cat` of an agent-authored file
    # must not count as a recompute. Require the extractor to read from a
    # hash-pinned artifact (`extracts_from` + `extracts_from_sha256`) produced
    # by the recorded run. The hash is recomputed here and must match — so the
    # the agent cannot fabricate the number without also pinning (and being bound
    # to) the exact bytes of a real output artifact.
    extracts_from = record.get("extracts_from") or policy.get("extracts_from")
    extracts_hash = record.get("extracts_from_sha256") or policy.get("extracts_from_sha256")
    if not extracts_from or not isinstance(extracts_hash, str) or not SHA256_RE.fullmatch(extracts_hash):
        errors.append(
            f"{path}: metric_recompute evidence {evidence_id} requires extracts_from + "
            "extracts_from_sha256 (64-hex) pinning the real output artifact the extractor reads; "
            "a bare echo/cat of a self-authored value is not a recompute"
        )
        return
    artifact_path = root / str(extracts_from)
    if not artifact_path.exists():
        errors.append(f"{path}: metric_recompute evidence {evidence_id} extracts_from {extracts_from!r} does not exist")
        return
    if sha256(artifact_path) != extracts_hash:
        errors.append(
            f"{path}: metric_recompute evidence {evidence_id} extracts_from sha256 mismatch — "
            "the artifact has changed since the recompute was recorded"
        )
        return
    # ATTESTED MODE (V5): in addition to the hash pin above, require the artifact
    # to be a platform-attested command output — i.e. bytes a real Bash command
    # produced under the harness, signed by a key the agent cannot touch. This
    # closes the "agent writes a fake train-log.txt and pins its own hash"
    # residual that hash-pinning alone leaves open. When attested_outputs is
    # provided (suite ran with --attested), extracts_from MUST resolve to one of
    # the captured stdout files under .bagel/attestations/outputs/, and that
    # attestation's stdout_sha256 must equal extracts_from_sha256.
    if attested_outputs is not None:
        attested = None
        for _cmd, att in attested_outputs.items():
            if att.get("stdout_sha256") == extracts_hash:
                attested = att
                break
        if attested is None:
            errors.append(
                f"{path}: metric_recompute evidence {evidence_id} extracts_from is not bound to "
                "any platform-attested Bash command output (no attestation with matching "
                "stdout_sha256). Under --attested mode, the metric must trace to bytes a real "
                "command produced under the harness, not an agent-authored file."
            )
            return
        # Non-triviality: the attested command must look like real training/eval,
        # not a one-line echo/cat/print/python -c of a number. Two requirements:
        #   (1) the command runs a real compute entry-point (python script, torchrun,
        #       train/eval subcommand) AND is not an inline one-liner (`-c`, `-e`),
        #   (2) the attested stdout is non-trivially sized (a bare number is <32 bytes).
        # Heuristic, not proof, but raises fabrication cost from "2 min YAML" to
        # "must run a substantive command that produces a real-looking log".
        cmd = str(attested.get("command") or "")
        is_inline = bool(re.search(r"\b(-c|-e|--command)\b\s+[\"']", cmd))
        has_entrypoint = bool(re.search(r"(torchrun|accelerate|python\s+\S+\.(py|ipynb)|julia\s+\S+\.jl|R\s+--file|Rscript\s+\S+|node\s+\S+\.js|cargo\s+run|go\s+run|make\s+\S+|\btrain\b|\beval\b|\bbenchmark\b|\bfit\b|\brun\b.*\.(py|sh))", cmd, re.I))
        has_trivial_producer = bool(re.search(r"^\s*(echo|cat|printf|tee)\s|print\s*\(", cmd, re.I))
        stdout_bytes = int(attested.get("stdout_bytes") or 0)
        if is_inline or has_trivial_producer or not has_entrypoint:
            errors.append(
                f"{path}: metric_recompute evidence {evidence_id} attested command {cmd!r} does not "
                "look like a genuine training/eval run (inline -c/-e one-liner, trivial echo/cat/print "
                "producer, or no compute entry-point like train.py/eval.py). Under --attested mode the "
                "metric must come from a substantive script/entry-point command."
            )
            return
        if stdout_bytes < 32:
            errors.append(
                f"{path}: metric_recompute evidence {evidence_id} attested command produced only "
                f"{stdout_bytes} bytes of stdout — a real training/eval log should be larger; "
                "this looks like a trivial producer rather than a genuine run."
            )
            return
    # Refuse extractors that cannot have read the pinned artifact: the extractor
    # text must reference the extracts_from path, otherwise a `echo 0.847` still
    # passes the hash check by ignoring the artifact entirely.
    if str(extracts_from) not in str(extractor):
        errors.append(
            f"{path}: metric_recompute evidence {evidence_id} metric_extractor must reference "
            f"extracts_from ({extracts_from!r}); an extractor that ignores the pinned artifact "
            "is not a genuine recompute"
        )
        return
    cwd = root / str(record.get("cwd") or ".")
    result = subprocess.run(str(extractor), shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
    if result.returncode != 0:
        errors.append(f"{path}: metric_extractor for {evidence_id} exited {result.returncode}: {result.stderr[-200:]}")
        return
    recomputed = extract_number(result.stdout, str(metric_name) if metric_name else None)
    if recomputed is None or not math.isfinite(recomputed):
        errors.append(f"{path}: metric_extractor for {evidence_id} did not print a finite numeric metric")
        return
    if abs(float(recomputed) - float(declared)) > float(tolerance):
        errors.append(
            f"{path}: metric_recompute {evidence_id} recomputed {recomputed} but declared "
            f"{declared} with tolerance {tolerance}"
        )


def collect_records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    base = root / ".bagel/evidence"
    if not base.exists():
        return out
    for path in sorted(base.rglob("*.yaml")):
        data = load_yaml(path, {})
        if isinstance(data, dict) and ("evidence" in data or "evidence_id" in data):
            rows = as_list(data.get("evidence")) if "evidence" in data else [data]
        elif isinstance(data, list):
            rows = data
        else:
            continue
        for row in rows:
            rec = as_dict(row)
            if rec.get("evidence_id") or rec.get("command"):
                out.append((path, rec))
    return out


def git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def referenced_evidence(root: Path) -> list[str]:
    refs: list[str] = []
    progress = load_yaml(root / ".bagel/evidence/progress-deltas.yaml", [])
    for row in as_list(progress):
        refs.extend(str(item) for item in as_list(as_dict(row).get("evidence")))
    for path in (root / ".bagel/telemetry").glob("cycles*.yaml") if (root / ".bagel/telemetry").exists() else []:
        data = load_yaml(path, {})
        rows = data.get("cycles") if isinstance(data, dict) else data
        for row in as_list(rows):
            refs.extend(str(item) for item in as_list(as_dict(as_dict(row).get("outputs")).get("evidence_refs")))
    return [ref for ref in refs if ref and ref != "None"]


def validate(root: Path, replay: bool = False, attested_outputs: dict[str, dict[str, Any]] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    records = collect_records(root)
    refs = referenced_evidence(root)
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    build_started = state.get("phase") in {"Build", "Iterate", "Polish"} or bool(state.get("task_queue"))
    if not records:
        if refs or build_started:
            errors.append("evidence references or Build state exist but no indexed evidence records were found")
        return errors, warnings
    record_ids = {str(as_dict(record).get("evidence_id")) for _, record in records if as_dict(record).get("evidence_id")}
    record_paths = {str(path.relative_to(root)) for path, _ in records}
    for ref in refs:
        if ref.startswith("EV-") and ref not in record_ids:
            errors.append(f"referenced evidence_id has no validated evidence record: {ref}")
        elif ref.startswith(".bagel/evidence/") and ref not in record_paths and not (root / ref).exists():
            errors.append(f"referenced evidence path does not exist: {ref}")
    current_head = git_head(root)
    hash_history: dict[tuple[str, str], int] = {}

    for path, record in records:
        policy = as_dict(record.get("replay_policy"))
        mode = policy.get("mode")
        if mode not in {"exact", "sampled", "not_replayable", "metric_recompute"}:
            errors.append(f"{path}: evidence {record.get('evidence_id', '<unknown>')} replay_policy.mode must be exact|sampled|not_replayable|metric_recompute")
            continue
        if mode == "metric_recompute":
            validate_metric_recompute(root, path, record, policy, errors, attested_outputs)
            # Metric recompute reads saved logs/results and does not need to rerun expensive training.
            continue
        if mode == "not_replayable":
            if not record.get("evidence_id"):
                errors.append(f"{path}: not_replayable evidence requires evidence_id")
            if not policy.get("reason_if_not_replayable"):
                errors.append(f"{path}: not_replayable evidence requires reason_if_not_replayable")
            if not record.get("manual_evidence_reviewer"):
                errors.append(f"{path}: not_replayable evidence requires manual_evidence_reviewer")
            if record.get("command") and policy.get("reason_if_not_replayable") not in {"external_resource", "privacy_sensitive", "paid_or_rate_limited", "manual_visual_judgment", "time_dependent"}:
                errors.append(f"{path}: command-like not_replayable evidence requires an allowed reason enum")
            if record.get("metric_extractor") or policy.get("metric_extractor"):
                validate_metric_recompute(root, path, record, policy, errors, attested_outputs)
            continue

        missing = sorted(field for field in REQUIRED_RUNNABLE if field not in record)
        if missing:
            errors.append(f"{path}: runnable evidence missing fields: {', '.join(missing)}")
            continue
        for key in ("stdout_path", "stderr_path"):
            p = root / str(record.get(key))
            if not p.exists():
                errors.append(f"{path}: {key} missing file {record.get(key)}")
                continue
            expected = record.get(key.replace("_path", "_sha256"))
            if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
                errors.append(f"{path}: {key.replace('_path', '_sha256')} must be a non-empty lowercase 64-char sha256")
                continue
            actual = sha256(p)
            if actual != expected:
                errors.append(f"{path}: {key} hash mismatch for {record.get(key)}")
        if current_head and record.get("git_ref") and str(record.get("git_ref")) != current_head:
            if mode == "exact" or state.get("run_status") == "complete" or state.get("status") == "complete":
                errors.append(f"{path}: exact/final evidence git_ref differs from current HEAD")
            else:
                warnings.append(f"{path}: evidence git_ref differs from current HEAD; replay may require checkout")
        key = (str(record.get("command")), str(record.get("stdout_sha256")))
        hash_history[key] = hash_history.get(key, 0) + 1
        if hash_history[key] >= 3:
            warnings.append(f"{path}: same command/stdout hash reused {hash_history[key]} times; confirm evidence is not stale")
        if replay and mode == "exact" and str(record.get("git_ref")) == current_head:
            cwd = root / str(record.get("cwd") or ".")
            result = subprocess.run(str(record["command"]), shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, timeout=120)
            nondet_note = policy.get("nondeterminism_note")
            nondet_bound = policy.get("expected_nondeterminism_bound")
            if nondet_note and not nondet_bound:
                errors.append(f"{path}: nondeterminism_note requires expected_nondeterminism_bound; it is not a blanket replay waiver")
            if result.returncode != record.get("exit_code") and not nondet_bound:
                errors.append(f"{path}: replay exit code {result.returncode} != recorded {record.get('exit_code')}")
            for stream, actual_bytes in (("stdout", result.stdout), ("stderr", result.stderr)):
                compare = policy.get(f"compare_{stream}", "normalized" if mode == "exact" else "ignore")
                recorded_path = root / str(record.get(f"{stream}_path"))
                if compare == "ignore":
                    continue
                if not recorded_path.exists():
                    errors.append(f"{path}: replay compare_{stream} requested but recorded file missing")
                    continue
                recorded = recorded_path.read_bytes()
                if compare == "exact" and actual_bytes != recorded and not nondet_bound:
                    errors.append(f"{path}: replay {stream} differs from recorded {stream}")
                elif compare == "normalized" and normalize_bytes(actual_bytes) != normalize_bytes(recorded) and not nondet_bound:
                    errors.append(f"{path}: replay normalized {stream} differs from recorded {stream}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--replay", action="store_true", help="Rerun exact commands when git_ref matches current HEAD")
    parser.add_argument("--attested", action="store_true",
                        help="Require metric_recompute extracts_from to bind to a platform-attested "
                             "Bash command output (V5 ground-truth mode). When the attestation tier "
                             "is unavailable, this flag is a no-op and the run is reported UNATTESTED.")
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()

    attested_outputs: dict[str, dict[str, Any]] | None = None
    if args.attested:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            import attestation_lib as al
            if al.has_key():
                _errs, verified = al.validate_chain(Path(args.root).resolve(), al.get_key())
                attested_outputs = al.index_outputs(verified)
        except Exception:
            # Attestation lib unavailable or chain broken — attestation_check.py
            # (run first in the suite) will have already failed loudly. Here we
            # just fall back to unattested so evidence_replay doesn't double-report.
            attested_outputs = None

    errors, warnings = validate(Path(args.root).resolve(), replay=args.replay, attested_outputs=attested_outputs)
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL evidence replay check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
