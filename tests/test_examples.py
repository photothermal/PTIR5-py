"""Smoke-test the example scripts as a user would run them.

Labels in the fixtures contain non-ASCII text such as ``cm⁻¹``. Windows writes
redirected output in its ANSI code page (cp1252), which cannot encode it, so
each run forces that encoding to reproduce the problem on any platform.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((PROJECT_ROOT / "examples").glob("*.py"))


@pytest.mark.parametrize("script", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_example_runs_with_a_legacy_output_encoding(script: Path) -> None:
    env = {
        **os.environ,
        "PYTHONIOENCODING": "cp1252",
        "PYTHONPATH": str(PROJECT_ROOT / "src"),
    }
    env.pop("PYTHONUTF8", None)
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
