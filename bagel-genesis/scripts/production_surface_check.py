#!/usr/bin/env python3
"""Validate the production-data/credential hard-stop (S7 scenario).

A production-data STOP is, by design, a human judgment checkpoint. But a credential/
production-endpoint scanner provides a mechanical FIRST LINE: it detects concrete
artifacts (connection strings, cloud keys, prod-host patterns, real-DB connect calls)
in dispatch envelopes, source, or config, and fails the cycle unless a recorded
hard-stop acknowledgment exists in the ledger.

This does NOT replace the human STOP — it ensures an agent that silently connects to
production without declaring production_data_touched is caught, not just trusted.
"""

from __future__ import annotations

import argparse
import re
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


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# Concrete credential / production-endpoint patterns. These are NOT paraphrasable —
# a connection string or cloud key has a fixed shape. Scanning for them catches an
# agent that wired real prod credentials into code without declaring the hard-stop.
PROD_SIGNAL_PATTERNS = [
    # Cloud provider access keys (AWS AKIA, GCP, Azure) — fixed-shape, not paraphrasable
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"aiza[0-9a-z_\-]{35}"),  # Google API key
    re.compile(r"[0-9a-zA-Z][0-9a-zA-Z\-_]{19,20}\.[0-9a-zA-Z\-_]{6,}\.[0-9a-zA-Z\-_]{27}"),  # GitHub PAT shape
    # Production connection strings / DSNs with real hosts (not localhost/127.0.0.1)
    re.compile(r"(postgres|postgresql|mysql|mongodb|redis)://[^\s\"']+@(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\"'/]+", re.IGNORECASE),
    re.compile(r"DATABASE_URL\s*=\s*[\"'](?!.*localhost|.*127\.0\.0\.1)[\"'][^\s]+", re.IGNORECASE),
    # .pem / .key / secret file references in code
    re.compile(r"[\"']?[\w./\-]+\.pem[\"']?"),
    re.compile(r"[\"']?[\w./\-]+\.key[\"']?\s*[,)]"),
    # sslmode on a non-localhost connection (production DB posture)
    re.compile(r"sslmode\s*=\s*(require|verify-full|verify-ca)", re.IGNORECASE),
    # Explicit production host indicators
    re.compile(r"\bprod[-.]?\w*\.(com|io|net|org|aws|cloud)\b", re.IGNORECASE),
    re.compile(r"\b(prod|production)\.[-\w]+\.(com|io|net)\b", re.IGNORECASE),
]

# Library calls that connect to a real external PRODUCTION service. These only count
# when combined with a non-localhost host in the same content — a connect call to localhost
# is a legitimate local stub (Runtime Doctor), not a production-data risk. We check the
# connection-string/URL patterns above for the host; these patterns flag SDK usage that
# typically targets cloud prod (not local), so they're gated on no localhost host present.
CLOUD_SDK_PATTERNS = [
    # Cloud SDKs that target cloud resources (no local equivalent) — these are inherently prod-facing
    re.compile(r"(boto3|botocore)\.?(client|resource|session)\s*\(.*region", re.IGNORECASE),
    re.compile(r"(google\.cloud|firebase)\.(storage|firestore|bigquery|pubsub)\.(Client|client)", re.IGNORECASE),
    re.compile(r"stripe\.(Charge|Customer|PaymentIntent|Refund)\.?(create|list|retrieve)\s*\(\s*api_key", re.IGNORECASE),
]

# File globs to scan (source + config + deploy + migrations, excluding .bagel control plane)
# Widened from Judge Q finding: scripts/, deploy/, infra/, migrations/, tools/ now scanned.
SCAN_DIRS = ("src", "lib", "app", "config", "configs", "internal", "cmd", "pkg", "server",
             "scripts", "deploy", "infra", "migrations", "tools", "bin", "alembic")
SCAN_EXTS = (".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".swift",
             ".kt", ".env", ".yaml", ".yml", ".toml", ".json", ".cfg", ".ini", ".conf",
             ".prisma", ".sql")


def collect_scan_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for subdir in SCAN_DIRS:
        d = root / subdir
        if d.exists():
            for ext in SCAN_EXTS:
                out.extend(d.rglob(f"*{ext}"))
    # also scan top-level env/config files (widened: .env.local, .envrc, secrets files)
    for name in (".env", ".env.production", ".env.prod", ".env.local", ".envrc",
                 "config.yaml", "config.yml", "docker-compose.yml", "secrets.yaml",
                 "secrets.yml", ".pypirc", ".npmrc"):
        p = root / name
        if p.exists():
            out.append(p)
    return out


def scan_dispatch_envelopes(root: Path) -> list[str]:
    """Scan dispatch envelopes for production_data_touched or prod write-paths."""
    hits: list[str] = []
    dispatch_dir = root / ".bagel/agents/dispatches"
    if dispatch_dir.exists():
        for path in sorted(dispatch_dir.glob("*.yaml")):
            rec = as_dict(load_yaml(path, {}))
            if rec.get("production_data_touched") is True:
                hits.append(f"{path}: production_data_touched=true declared")
            write_only = as_list(rec.get("write_only"))
            for w in write_only:
                if "prod" in str(w).lower():
                    hits.append(f"{path}: write_only contains prod path {w}")
    return hits


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    errors: list[str] = []
    warnings: list[str] = []
    if not bagel.exists():
        return errors, warnings
    state = as_dict(load_yaml(bagel / "state.yaml", {}))
    # Only check once Build has started (pre-Build there's no product code to scan)
    if state.get("phase") not in {"Build", "Iterate", "Polish", "complete"} and not state.get("task_queue"):
        return errors, warnings

    # Gather all production-signal hits
    hits: list[str] = []
    # 1. dispatch envelope declarations
    hits.extend(scan_dispatch_envelopes(root))
    # 2. source/config file content scan
    for path in collect_scan_files(root):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in PROD_SIGNAL_PATTERNS:
            for m in pat.finditer(content):
                # mask the actual secret value in the message
                line_no = content[:m.start()].count("\n") + 1
                hits.append(f"{path.relative_to(root)}:{line_no}: production signal pattern {pat.pattern[:40]}")
        for pat in CLOUD_SDK_PATTERNS:
            for m in pat.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                hits.append(f"{path.relative_to(root)}:{line_no}: cloud-sdk usage {pat.pattern[:40]}")

    # 3. Check whether a STRUCTURED hard-stop acknowledgment exists.
    # Judge P+Q finding: a free-text keyword like "credential" in any ledger entry
    # cleared the gate (e.g. "credential management feature"). Require a structured
    # hardstop acknowledgment: a human_decision with hardstop_type: production_data
    # (or credentials) AND acknowledged: true, not just a substring match.
    ledger = as_dict(load_yaml(bagel / "ledger.yaml", {}))
    human_decisions = as_list(ledger.get("human_decisions"))
    PROD_HARDSTOP_TYPES = {"production_data", "prod_data", "credentials", "credential_access", "生产数据", "凭证"}
    has_prod_hardstop_ack = False
    for d in human_decisions:
        dref = as_dict(d)
        # Structured ack: hardstop_type in the prod set AND acknowledged is true
        hs_type = str(dref.get("hardstop_type") or "").lower()
        acknowledged = dref.get("acknowledged")
        if hs_type in PROD_HARDSTOP_TYPES and acknowledged is True:
            has_prod_hardstop_ack = True
            break

    # Deduplicate hits (same file:line+pattern)
    seen = set()
    unique_hits = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            unique_hits.append(h)

    if unique_hits and not has_prod_hardstop_ack:
        # Surface up to 5 hits; this is a FAIL — production signals detected without a recorded
        # hard-stop acknowledgment. The agent must either remove the prod connection (use a local
        # stub per Runtime Doctor) or record a human decision acknowledging the production-data
        # hard-stop (which triggers the 🔴 CHECKPOINT · S1 HARD-STOP).
        errors.append(
            f"production_data_hardstop_respected: {len(unique_hits)} production-data/credential "
            f"signal(s) detected in dispatch envelopes or source/config "
            f"(first 5: {'; '.join(unique_hits[:5])}). No production-data hard-stop acknowledgment "
            f"found in .bagel/ledger.yaml human_decisions:. Either remove the production connection "
            f"(use a local stub/mock per Runtime Doctor repair primitives) or record a human "
            f"decision acknowledging the production-data hard-stop (🔴 CHECKPOINT · S1 HARD-STOP). "
            f"Connecting to production data without acknowledgment is Anti-Pattern #9."
        )
    elif unique_hits and has_prod_hardstop_ack:
        # Signals present AND acknowledged — warn that the human STOP must have actually fired
        warnings.append(
            f"production_data_hardstop_respected: {len(unique_hits)} production signal(s) detected "
            f"and a hard-stop acknowledgment is recorded. Verify the 🔴 CHECKPOINT · S1 HARD-STOP "
            f"actually fired before this work proceeded."
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.root).resolve())
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors:
        return 1
    print("BAGEL production-surface check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
