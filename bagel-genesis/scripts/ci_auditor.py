#!/usr/bin/env python3
"""CI-side research auditor — the layer the agent cannot reach.

Runs in CI where the signing private key is available only to the runner.
It binds headline research claims to committed git bytes, not to agent-authored
YAML assertions.

Checks:
  1. PLAN-BEFORE-RUNS: experiment-plan.yaml and preregistration.yaml must first
     appear in commits strictly before any result-producing artifact.
  2. PLAN CONTENT PIN: preregistration.yaml pins plan path/hash/commit; state
     or constitution hashes are not accepted as CI authority.
  3. METRIC RECOMPUTE: every headline metric is recomputed from committed,
     hash-pinned artifacts through preregistered command_ref entrypoints.
     Trivial extractors and unpinned commands are rejected.
  4. STATISTIC RECOMPUTE: per-seed statistics must read seed values from
     run_ref evidence; YAML literal seed values are refused.
  5. ASYMMETRIC VERDICT: verdicts are signed with BAGEL_AUDIT_PRIVATE_KEY_PEM
     via openssl and verified locally with the committed public key.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
TRIVIAL_EXTRACTOR_RE = re.compile(r"^\s*(echo|printf|cat|tee)\b|\bpython\s+-c\b|\bnode\s+-e\b|\bperl\s+-e\b", re.I)
COMPUTE_ENTRYPOINT_RE = re.compile(
    r"(torchrun|accelerate|python\s+\S+\.(py|ipynb)|Rscript\s+\S+|R\s+--file|"
    r"julia\s+\S+\.jl|node\s+\S+\.js|cargo\s+run|go\s+run|make\s+\S+|"
    r"\b(train|eval|evaluate|benchmark|aggregate|verify|run)\b)",
    re.I,
)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_show(root: Path, commit: str, path: str) -> bytes | None:
    result = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True)
    return result.stdout if result.returncode == 0 else None


def load_yaml_bytes(raw: bytes | None) -> Any:
    if raw is None:
        return None
    try:
        return yaml.safe_load(raw)
    except Exception:
        return None


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_yaml_bytes(body: dict[str, Any]) -> bytes:
    return yaml.safe_dump(body, sort_keys=True).encode()


def first_commit_introducing(root: Path, path: str, head: str) -> str | None:
    out = run_git(root, "log", "--diff-filter=A", "--format=%H", head, "--", path)
    commits = [line for line in out.splitlines() if line.strip()]
    return commits[-1].strip() if commits else None


def commit_index(root: Path, commit: str, head: str) -> int | None:
    commits = [line for line in run_git(root, "rev-list", "--reverse", head).splitlines() if line]
    try:
        return commits.index(commit)
    except ValueError:
        return None


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        capture_output=True,
    )
    return result.returncode == 0


def extract_number(stdout: str) -> float | None:
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", stdout)
    for item in reversed(nums):
        value = float(item)
        if math.isfinite(value):
            return value
    return None


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))


def recompute_statistic(per_seed_values: list[float]) -> tuple[float | None, str]:
    n = len(per_seed_values)
    if n < 2:
        return None, "insufficient"
    mean = sum(per_seed_values) / n
    var = sum((x - mean) ** 2 for x in per_seed_values) / (n - 1)
    se = math.sqrt(var / n)
    if se == 0:
        return None, "zero_variance"
    t = mean / se
    p = 2 * (1 - _norm_cdf(abs(t)))
    return p, f"paired_t_normal_approx(n={n},t={t:.3f})"


def normalize_evidence(data: Any) -> dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get("evidence"), list):
        return data["evidence"][0] if data["evidence"] else {}
    return data if isinstance(data, dict) else {}


def load_evidence(root: Path, head: str, ref: str) -> dict[str, Any] | None:
    raw = git_show(root, head, ref)
    if raw is None:
        return None
    return normalize_evidence(load_yaml_bytes(raw))


def command_pins(prereg: dict[str, Any]) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in prereg.get("command_pins") or []:
        if not isinstance(raw, dict):
            continue
        path = raw.get("path") or raw.get("command_ref")
        digest = raw.get("sha256") or raw.get("command_sha256")
        if isinstance(path, str) and isinstance(digest, str):
            pins[path] = digest
    return pins


def validate_command_ref(root: Path, head: str, ev: dict[str, Any], ref: str, prereg: dict[str, Any], errors: list[str]) -> str | None:
    policy = ev.get("replay_policy") or {}
    command_ref = ev.get("command_ref") or policy.get("command_ref")
    if not isinstance(command_ref, str) or not command_ref:
        errors.append(f"metric_recompute: evidence {ref} requires command_ref pinned in preregistration.yaml")
        return None
    expected = command_pins(prereg).get(command_ref)
    if not expected:
        errors.append(f"metric_recompute: evidence {ref} command_ref {command_ref!r} is not pinned in preregistration.yaml command_pins")
        return None
    if not SHA256_RE.fullmatch(str(expected)):
        errors.append(f"metric_recompute: command_ref {command_ref!r} has invalid preregistered sha256")
        return None
    command_bytes = git_show(root, head, command_ref)
    if command_bytes is None:
        errors.append(f"metric_recompute: command_ref {command_ref!r} not in commit {head[:10]}")
        return None
    actual = sha256_bytes(command_bytes)
    if actual != expected:
        errors.append(
            f"metric_recompute: command_ref {command_ref!r} sha256 mismatch "
            f"({actual[:16]} != preregistered {expected[:16]})"
        )
        return None
    return command_ref


def validate_extractor_shape(ev: dict[str, Any], ref: str, errors: list[str]) -> tuple[str, str, str, float, float] | None:
    policy = ev.get("replay_policy") or {}
    extractor = ev.get("metric_extractor") or policy.get("metric_extractor")
    extracts_from = ev.get("extracts_from") or policy.get("extracts_from")
    extracts_hash = ev.get("extracts_from_sha256") or policy.get("extracts_from_sha256")
    declared = ev.get("declared_value", policy.get("declared_value"))
    tolerance = ev.get("recompute_tolerance", policy.get("recompute_tolerance", 0))
    if not (extractor and extracts_from and isinstance(declared, (int, float))):
        errors.append(f"metric_recompute: evidence {ref} missing extractor/extracts_from/declared_value")
        return None
    if not isinstance(extracts_hash, str) or not SHA256_RE.fullmatch(extracts_hash):
        errors.append(f"metric_recompute: evidence {ref} requires extracts_from_sha256 (64 lowercase hex)")
        return None
    if str(extracts_from) not in str(extractor):
        errors.append(
            f"metric_recompute: evidence {ref} extractor must reference extracts_from "
            f"{extracts_from!r}; ignoring the artifact is not a recompute"
        )
        return None
    if TRIVIAL_EXTRACTOR_RE.search(str(extractor)) and not COMPUTE_ENTRYPOINT_RE.search(str(extractor)):
        errors.append(
            f"metric_recompute: evidence {ref} extractor {extractor!r} is a trivial producer "
            "rather than a substantive recompute"
        )
        return None
    try:
        return str(extractor), str(extracts_from), str(extracts_hash), float(declared), float(tolerance)
    except (TypeError, ValueError):
        errors.append(f"metric_recompute: evidence {ref} has non-numeric declared_value or tolerance")
        return None


def recompute_metric_from_evidence(root: Path, head: str, ref: str, errors: list[str]) -> float | None:
    prereg = load_preregistration(root, head)
    ev = load_evidence(root, head, ref)
    if ev is None:
        errors.append(f"metric_recompute: evidence_ref {ref!r} not in commit {head[:10]}")
        return None
    policy = ev.get("replay_policy") or {}
    if policy.get("mode") not in {"metric_recompute", "not_replayable"} and not ev.get("metric_extractor"):
        errors.append(f"metric_recompute: evidence {ref} is not a metric_recompute record")
        return None
    shape = validate_extractor_shape(ev, ref, errors)
    if shape is None:
        return None
    extractor, extracts_from, extracts_hash, declared, tolerance = shape
    command_ref = validate_command_ref(root, head, ev, ref, prereg, errors)
    if command_ref is None:
        return None
    if command_ref not in extractor:
        errors.append(
            f"metric_recompute: evidence {ref} extractor must invoke pinned command_ref "
            f"{command_ref!r}; unpinned scripts such as cheat.py are refused"
        )
        return None
    artifact = git_show(root, head, extracts_from)
    if artifact is None:
        errors.append(f"metric_recompute: extracts_from {extracts_from!r} not in commit {head[:10]}")
        return None
    actual_hash = sha256_bytes(artifact)
    if actual_hash != extracts_hash:
        errors.append(
            f"metric_recompute: {ref} extracts_from sha256 mismatch "
            f"({actual_hash[:16]} != {extracts_hash[:16]})"
        )
        return None
    with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as tmp:
        tmp.write(artifact)
        tmp_path = tmp.name
    try:
        cmd = extractor.replace(extracts_from, tmp_path)
        result = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            errors.append(f"metric_recompute: extractor for {ref} exited {result.returncode}")
            return None
        if len(result.stdout.encode()) < 8:
            errors.append(f"metric_recompute: extractor for {ref} produced too little output to audit")
            return None
        recomputed = extract_number(result.stdout)
        if recomputed is None:
            errors.append(f"metric_recompute: extractor for {ref} produced no number")
            return None
        if abs(recomputed - declared) > tolerance:
            errors.append(
                f"metric_recompute: {ref} recomputed {recomputed} vs declared {declared} "
                f"(tol {tolerance})"
            )
            return None
        return recomputed
    finally:
        os.unlink(tmp_path)


def evidence_artifact_identity(root: Path, head: str, ref: str) -> tuple[str, str, str]:
    ev = load_evidence(root, head, ref) or {}
    policy = ev.get("replay_policy") or {}
    return (
        str(ev.get("extracts_from") or policy.get("extracts_from") or ""),
        str(ev.get("extracts_from_sha256") or policy.get("extracts_from_sha256") or ""),
        str(ev.get("attestation_id") or policy.get("attestation_id") or ""),
    )


def evidence_seed(root: Path, head: str, ref: str) -> Any:
    ev = load_evidence(root, head, ref) or {}
    if "seed" in ev:
        return ev.get("seed")
    metadata = ev.get("metadata")
    return metadata.get("seed") if isinstance(metadata, dict) else None


def load_preregistration(root: Path, head: str) -> dict[str, Any]:
    data = load_yaml_bytes(git_show(root, head, ".bagel/research/preregistration.yaml"))
    return (data.get("preregistration") if isinstance(data, dict) else None) or (data if isinstance(data, dict) else {})


def validate_public_key_pin(root: Path, head: str, prereg: dict[str, Any], errors: list[str], notes: list[str]) -> None:
    expected = prereg.get("audit_public_key_sha256")
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        errors.append("audit_public_key_pin: preregistration.yaml requires audit_public_key_sha256 (64 lowercase hex)")
        return
    pub = git_show(root, head, ".bagel/audit/ci-audit-public.pem")
    if pub is None:
        errors.append("audit_public_key_pin: .bagel/audit/ci-audit-public.pem missing at audited commit")
        return
    actual = sha256_bytes(pub)
    if actual != expected:
        errors.append(f"audit_public_key_pin: public key sha256 {actual[:16]} != preregistered {expected[:16]}")
    else:
        notes.append("audit_public_key_pin: committed public key matches preregistration.yaml")


def validate_prereg_frozen(root: Path, head: str, prereg_commit: str | None, errors: list[str], notes: list[str]) -> None:
    if not prereg_commit:
        return
    first = git_show(root, prereg_commit, ".bagel/research/preregistration.yaml")
    current = git_show(root, head, ".bagel/research/preregistration.yaml")
    if first is None or current is None:
        errors.append("preregistration_frozen: cannot read preregistration at first commit and HEAD")
        return
    if sha256_bytes(first) != sha256_bytes(current):
        errors.append(
            "preregistration_frozen: preregistration.yaml changed after its first pre-result commit; "
            "post-hoc command pins or public-key pins are refused"
        )
    else:
        notes.append("preregistration_frozen: preregistration bytes unchanged since first commit")


def earliest_result_commit(root: Path, head: str) -> str | None:
    earliest: tuple[int, str] | None = None
    paths = [
        ".bagel/research/claim-evidence.yaml",
        ".bagel/research/experiment-log.yaml",
    ]
    for path in paths:
        commit = first_commit_introducing(root, path, head)
        if not commit:
            continue
        idx = commit_index(root, commit, head)
        if idx is not None and (earliest is None or idx < earliest[0]):
            earliest = (idx, commit)
    return earliest[1] if earliest else None


def audit(root: Path, head: str | None) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    notes: list[str] = []
    if head is None:
        head = run_git(root, "rev-parse", "HEAD")
    short = head[:10]

    plan_bytes = git_show(root, head, ".bagel/research/experiment-plan.yaml")
    if not plan_bytes:
        return errors, notes, {"head": head, "short": short, "verdict": "no_research_plan"}

    plan_commit = first_commit_introducing(root, ".bagel/research/experiment-plan.yaml", head)
    prereg_commit = first_commit_introducing(root, ".bagel/research/preregistration.yaml", head)
    result_commit = earliest_result_commit(root, head)

    if plan_commit and result_commit:
        plan_i = commit_index(root, plan_commit, head)
        result_i = commit_index(root, result_commit, head)
        if plan_commit == result_commit or plan_i is None or result_i is None or plan_i >= result_i:
            errors.append(
                f"HARKing_git: plan first appeared in {plan_commit[:10]} and result artifact "
                f"first appeared in {result_commit[:10]}; plan must be committed strictly before results."
            )
        elif not is_ancestor(root, plan_commit, result_commit):
            errors.append(
                f"HARKing_git: plan@{plan_commit[:10]} is not an ancestor of results@{result_commit[:10]}"
            )
        else:
            notes.append(f"plan_before_runs: plan@{plan_commit[:10]} strictly precedes results@{result_commit[:10]}")

    prereg = load_preregistration(root, head)
    validate_public_key_pin(root, head, prereg, errors, notes)
    validate_prereg_frozen(root, head, prereg_commit, errors, notes)
    expected_hash = prereg.get("plan_sha256")
    expected_path = prereg.get("plan_path") or ".bagel/research/experiment-plan.yaml"
    expected_commit = prereg.get("plan_commit")
    if not prereg:
        errors.append("plan_content_pin: missing .bagel/research/preregistration.yaml")
    elif expected_path != ".bagel/research/experiment-plan.yaml":
        errors.append(f"plan_content_pin: preregistration plan_path must be .bagel/research/experiment-plan.yaml, got {expected_path!r}")
    elif not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
        errors.append("plan_content_pin: preregistration.yaml requires plan_sha256 (64 lowercase hex)")
    elif sha256_bytes(plan_bytes) != expected_hash:
        errors.append(
            f"plan_content_pin: experiment-plan.yaml sha256 at HEAD ({sha256_bytes(plan_bytes)[:16]}) "
            f"!= preregistered ({expected_hash[:16]})"
        )
    else:
        notes.append("plan_content_pin: plan sha matches preregistration.yaml")
    if expected_commit and plan_commit and expected_commit != plan_commit:
        errors.append(
            f"plan_content_pin: preregistration plan_commit {str(expected_commit)[:10]} "
            f"!= actual first plan commit {plan_commit[:10]}"
        )
    if prereg_commit and result_commit:
        prereg_i = commit_index(root, prereg_commit, head)
        result_i = commit_index(root, result_commit, head)
        if prereg_i is None or result_i is None or prereg_i >= result_i:
            errors.append(
                f"plan_content_pin: preregistration first appeared in {prereg_commit[:10]} "
                f"but results first appeared in {result_commit[:10]}; preregistration must predate results."
            )

    claim_bytes = git_show(root, head, ".bagel/research/claim-evidence.yaml")
    if claim_bytes:
        matrix = load_yaml_bytes(claim_bytes) or {}
        claims = (matrix.get("claim_evidence_matrix") or matrix).get("claims") or []
        for claim in claims:
            if not (claim.get("allowed_in_headline") or claim.get("is_headline")):
                continue
            metric_values = claim.get("metric_values") or []
            per_seed_values: list[float] = []
            per_seed_run_refs: list[str] = []
            per_seed_seeds: list[Any] = []
            per_seed_artifacts: list[tuple[str, str, str]] = []
            literal_per_seed = False
            for value in metric_values:
                if not isinstance(value, dict):
                    continue
                ref = value.get("evidence_ref") or value.get("evidence_id")
                if ref:
                    metric = recompute_metric_from_evidence(root, head, str(ref), errors)
                    if metric is not None:
                        notes.append(f"metric_recompute: {ref} recomputed {metric}")
                if value.get("run_ref"):
                    run_ref = str(value["run_ref"])
                    per_seed_run_refs.append(run_ref)
                    per_seed_seeds.append(value.get("seed"))
                    per_seed_artifacts.append(evidence_artifact_identity(root, head, run_ref))
                    ev_seed = evidence_seed(root, head, run_ref)
                    if value.get("seed") is None:
                        errors.append(f"statistic_recompute: claim {claim.get('claim_id')} run_ref {run_ref} missing metric_values.seed")
                    elif ev_seed is None:
                        errors.append(f"statistic_recompute: run_ref {run_ref} evidence missing seed binding")
                    elif str(ev_seed) != str(value.get("seed")):
                        errors.append(
                            f"statistic_recompute: run_ref {run_ref} seed {ev_seed!r} "
                            f"does not match metric_values.seed {value.get('seed')!r}"
                        )
                    seed_metric = recompute_metric_from_evidence(root, head, run_ref, errors)
                    if seed_metric is not None:
                        per_seed_values.append(float(seed_metric))
                elif isinstance(value.get("value"), (int, float)) and value.get("seed") is not None:
                    literal_per_seed = True
            if literal_per_seed:
                errors.append(
                    f"statistic_recompute: claim {claim.get('claim_id')} uses per-seed literal values "
                    "without run_ref provenance"
                )
            if per_seed_run_refs:
                if len(set(per_seed_run_refs)) != len(per_seed_run_refs):
                    errors.append(f"statistic_recompute: claim {claim.get('claim_id')} reuses a run_ref across seeds")
                if len(set(str(seed) for seed in per_seed_seeds)) != len(per_seed_seeds):
                    errors.append(f"statistic_recompute: claim {claim.get('claim_id')} has duplicate or missing seed values")
                artifact_pairs = [(a, h) for a, h, _att in per_seed_artifacts]
                if len(set(artifact_pairs)) != len(artifact_pairs):
                    errors.append(f"statistic_recompute: claim {claim.get('claim_id')} reuses extracts_from/extracts_from_sha256 across seeds")
                att_ids = [att for _a, _h, att in per_seed_artifacts if att]
                if att_ids and len(set(att_ids)) != len(att_ids):
                    errors.append(f"statistic_recompute: claim {claim.get('claim_id')} reuses attestation_id across seeds")
            if len(per_seed_values) >= 2:
                p, method = recompute_statistic(per_seed_values)
                sr_bytes = git_show(root, head, ".bagel/expert/statistical-rigor.yaml")
                sr = load_yaml_bytes(sr_bytes) if sr_bytes else {}
                declared_p = ((sr or {}).get("test_result") or {}).get("p_value") if isinstance(sr, dict) else None
                if p is None:
                    if isinstance(declared_p, (int, float)) and declared_p < 0.05:
                        errors.append(f"statistic_recompute: significant p_value declared but statistic recompute is {method}")
                else:
                    if isinstance(declared_p, (int, float)) and declared_p < 0.05 and p > 0.1:
                        errors.append(
                            f"statistic_recompute: declared p_value {declared_p} (<0.05) but "
                            f"per-seed run_ref recompute gives p≈{p:.3f} ({method})"
                        )
                    else:
                        notes.append(f"statistic_recompute: recomputed p≈{p:.3f} ({method})")
            elif per_seed_run_refs:
                sr_bytes = git_show(root, head, ".bagel/expert/statistical-rigor.yaml")
                sr = load_yaml_bytes(sr_bytes) if sr_bytes else {}
                declared_p = ((sr or {}).get("test_result") or {}).get("p_value") if isinstance(sr, dict) else None
                if isinstance(declared_p, (int, float)) and declared_p < 0.05:
                    errors.append("statistic_recompute: significant p_value declared but insufficient distinct per-seed evidence")

    verdict = "FAIL" if errors else "PASS"
    return errors, notes, {
        "head": head,
        "short": short,
        "verdict": verdict,
        "plan_commit": plan_commit,
        "prereg_commit": prereg_commit,
        "result_commit": result_commit,
    }


def sign_verdict(body: dict[str, Any]) -> str | None:
    pem = os.environ.get("BAGEL_AUDIT_PRIVATE_KEY_PEM")
    if not pem:
        return None
    canonical = canonical_yaml_bytes(body)
    with tempfile.NamedTemporaryFile("w", delete=False) as key_file, tempfile.NamedTemporaryFile("wb", delete=False) as body_file:
        key_file.write(pem)
        key_file.flush()
        body_file.write(canonical)
        body_file.flush()
        key_path = key_file.name
        body_path = body_file.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path, body_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
        return "openssl-sha256:" + base64.b64encode(result.stdout).decode("ascii")
    finally:
        os.unlink(key_path)
        os.unlink(body_path)


def write_verdict(root: Path, info: dict[str, Any], errors: list[str], notes: list[str]) -> Path:
    body = {
        "schema": "bagel_audit_verdict_v2",
        "commit": info["head"],
        "short": info["short"],
        "verdict": info["verdict"],
        "errors": errors,
        "notes": notes,
        "audited_at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip(),
    }
    sig = sign_verdict(body)
    if sig:
        body["signature"] = sig
        body["signature_key"] = "bagel-ci-audit-public-v1"
    out_dir = root / ".bagel/audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"VERDICT-{info['short']}.yaml"
    path.write_text(yaml.safe_dump(body, sort_keys=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("head", nargs="?", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        print("ci_auditor: not a git repo — auditor requires git history for DAG anchoring.")
        return 2
    errors, notes, info = audit(root, args.head)
    verdict_path = write_verdict(root, info, errors, notes)
    print(f"ci_auditor: verdict={info['verdict']} -> {verdict_path.name}")
    for note in notes:
        print(f"  note: {note}")
    for err in errors:
        print(f"  FAIL: {err}")
    if info["verdict"] == "PASS" and "BAGEL_AUDIT_PRIVATE_KEY_PEM" not in os.environ:
        print("  WARN: verdict is unsigned; configure BAGEL_AUDIT_PRIVATE_KEY_PEM in CI.")
    return 0 if info["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
