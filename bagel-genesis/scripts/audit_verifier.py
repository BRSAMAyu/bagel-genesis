#!/usr/bin/env python3
"""Local-side gate: verify a CI audit verdict for the current commit.

V4.1 research-grade closure uses asymmetric signatures:
  - CI signs with BAGEL_AUDIT_PRIVATE_KEY_PEM.
  - The project commits .bagel/audit/ci-audit-public.pem.
  - This verifier checks VERDICT-<HEAD>.yaml with openssl.

No Python crypto dependency is required.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def git_head(root: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def canonical_yaml_bytes(body: dict) -> bytes:
    return yaml.safe_dump(body, sort_keys=True).encode()


def public_key_pem(root: Path) -> str | None:
    env = os.environ.get("BAGEL_AUDIT_PUBLIC_KEY_PEM")
    if env:
        return env
    path = root / ".bagel/audit/ci-audit-public.pem"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def public_key_fingerprint(pem: str) -> str:
    return hashlib.sha256(pem.encode()).hexdigest()


def preregistration(root: Path, head: str) -> dict:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{head}:.bagel/research/preregistration.yaml"],
        capture_output=True,
    )
    if result.returncode == 0:
        data = yaml.safe_load(result.stdout) or {}
    else:
        path = root / ".bagel/research/preregistration.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    return (data.get("preregistration") if isinstance(data, dict) else None) or (data if isinstance(data, dict) else {})


def verify_signature(body: dict, public_pem: str) -> tuple[bool, str]:
    sig = str(body.get("signature") or "")
    if not sig.startswith("openssl-sha256:"):
        return False, "missing openssl-sha256 signature"
    signed = {k: v for k, v in body.items() if k not in {"signature", "signature_key"}}
    try:
        sig_bytes = base64.b64decode(sig.split(":", 1)[1], validate=True)
    except Exception as exc:
        return False, f"signature is not valid base64: {exc}"
    with tempfile.NamedTemporaryFile("w", delete=False) as key_file, tempfile.NamedTemporaryFile("wb", delete=False) as body_file, tempfile.NamedTemporaryFile("wb", delete=False) as sig_file:
        key_file.write(public_pem)
        key_file.flush()
        body_file.write(canonical_yaml_bytes(signed))
        body_file.flush()
        sig_file.write(sig_bytes)
        sig_file.flush()
        key_path = key_file.name
        body_path = body_file.name
        sig_path = sig_file.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", key_path, "-signature", sig_path, body_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip()
        return True, "signature valid"
    finally:
        for path in (key_path, body_path, sig_path):
            os.unlink(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    head = git_head(root)
    if not head:
        print("audit_verifier: NOT_AUDITED (not a git repo or no HEAD)")
        return 0

    short = head[:10]
    verdict_path = root / ".bagel/audit" / f"VERDICT-{short}.yaml"
    if not verdict_path.exists():
        print(f"audit_verifier: NOT_AUDITED (no CI verdict for {short}).")
        print("  Headline claims are shape-only. Run ci_auditor.py in CI to upgrade.")
        return 0

    body = yaml.safe_load(verdict_path.read_text(encoding="utf-8")) or {}
    verdict = str(body.get("verdict") or "UNKNOWN")
    stored_commit = str(body.get("commit") or "")
    if stored_commit and stored_commit != head:
        print(f"audit_verifier: STALE (verdict is for {stored_commit[:10]}, current HEAD is {short}).")
        return 0

    pub = public_key_pem(root)
    if not pub:
        print(f"audit_verifier: PRESENT_UNSIGNED (verdict {verdict} for {short}, no committed public key).")
        print("  Add .bagel/audit/ci-audit-public.pem or set BAGEL_AUDIT_PUBLIC_KEY_PEM.")
        return 0
    prereg = preregistration(root, head)
    actual_pub = public_key_fingerprint(pub)
    trust_anchor = os.environ.get("BAGEL_AUDIT_PUBLIC_KEY_SHA256")
    if not trust_anchor:
        print(f"audit_verifier: PRESENT_UNTRUSTED (verdict {verdict} for {short}, no out-of-band public-key fingerprint).")
        print("  Set BAGEL_AUDIT_PUBLIC_KEY_SHA256 from a reviewer/CI trust store before upgrading claims.")
        return 1
    if actual_pub != trust_anchor:
        print(
            f"audit_verifier: TAMPERED (public key fingerprint {actual_pub[:16]} "
            f"!= trusted {trust_anchor[:16]})."
        )
        return 1
    expected_pub = prereg.get("audit_public_key_sha256")
    if isinstance(expected_pub, str) and expected_pub and actual_pub != expected_pub:
        print(
            f"audit_verifier: TAMPERED (public key fingerprint {actual_pub[:16]} "
            f"!= preregistered {expected_pub[:16]})."
        )
        return 1
    ok, detail = verify_signature(body, pub)
    if not ok:
        print(f"audit_verifier: TAMPERED (verdict for {short} failed public-key verification: {detail}).")
        return 1

    if verdict == "PASS":
        print(f"audit_verifier: PASS_SIGNED (CI verdict for {short} is PASS, public-key signature valid).")
        print("  Headline claims upgraded to CI-verified.")
        return 0

    print(f"audit_verifier: FAIL_SIGNED (CI verdict for {short} is FAIL, public-key signature valid):")
    for err in (body.get("errors") or [])[:10]:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
