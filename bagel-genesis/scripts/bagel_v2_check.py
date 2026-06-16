#!/usr/bin/env python3
"""Compatibility wrapper for BAGEL V3.1 validator suite."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("bagel_v3_check.py")), run_name="__main__")
