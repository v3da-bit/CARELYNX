#!/usr/bin/env python3
"""Repo-root inference benchmark entrypoint (CLX-011). Delegates to infra/amd/benchmark_rocm.py."""

from __future__ import annotations

import runpy
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "infra" / "amd" / "benchmark_rocm.py"

if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
