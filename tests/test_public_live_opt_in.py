"""Explicit integration entry point; ordinary test runs never load credentials."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.environ.get("TINYERCOT_LIVE_TESTS") != "1",
    reason="Real public requests require TINYERCOT_LIVE_TESTS=1 and an installed wheel",
)
def test_installed_public_sources():
    """Run the bounded installed-wheel probe only on explicit operator request."""
    required = (
        "TINYERCOT_INSTALLED_PYTHON",
        "TINYERCOT_CREDENTIALS_FILE",
        "TINYERCOT_PROBE_OUTPUT",
    )
    if not all(os.environ.get(name) for name in required):
        pytest.fail("The three documented integration paths are required")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            os.environ[required[0]],
            "-I",
            str(root / "tools/probe_public.py"),
            "--live",
            "--credentials-file",
            os.environ[required[1]],
            "--output",
            os.environ[required[2]],
        ],
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        "Installed probe failed; inspect public receipt status"
    )
