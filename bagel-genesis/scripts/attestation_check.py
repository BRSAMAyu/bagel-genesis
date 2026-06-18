#!/usr/bin/env python3
"""Validate the platform attestation chain.

Reports one of three states:
  - UNATTESTED  : no BAGEL_ATTEST_KEY configured AND no attestations present.
                  The skill still works but every gate falls back to shape-only
                  (the pre-V5 residual disclosed in enforcement-honesty.md).
  - VERIFIED    : key present, attestations present, all signatures + chain OK.
  - TAMPERED    : signatures invalid, chain broken, or records present without key.

Exit codes: 0 = UNATTESTED or VERIFIED; 1 = TAMPERED (the suite must fail
loudly when the trust layer has been attacked, even if every other gate passes).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attestation_lib as al  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    key = al.get_key()
    records = al.load_records(root)

    if not records and key is None:
        print("attestation_check: UNATTESTED (no BAGEL_ATTEST_KEY, no attestations).")
        print("  Research gates fall back to shape-only (enforcement-honesty.md:39 residual).")
        print("  To enable ground-truth attestation: see references/platform-attestation.md.")
        return 0

    if not records and key is not None:
        print("attestation_check: UNATTESTED (key configured but no Bash commands attested yet).")
        return 0

    errors, verified = al.validate_chain(root, key)
    if errors:
        print("attestation_check: TAMPERED or misconfigured — chain/signature verification failed:")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    print(f"attestation_check: VERIFIED ({len(verified)} attested command outputs, signatures OK, chain intact).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
