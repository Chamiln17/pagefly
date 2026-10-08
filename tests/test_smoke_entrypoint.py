"""The smoke script's documented command must start, not just import under pytest."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_smoke_script_runs_as_documented():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.smoke_run", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr
    assert "--repair-demo" in result.stdout
    assert "uv run python -m scripts.smoke_run" in result.stdout
