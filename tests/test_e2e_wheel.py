"""Opt-in end to end: build the wheel and sdist, install the wheel, run the jpd script.

Slow and needs the ``build`` package, so it runs only with JSON_PRETTY_DIFF_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest
from conftest import FIXTURES, ROOT

import json_pretty_diff

pytestmark = pytest.mark.skipif(
    os.environ.get("JSON_PRETTY_DIFF_E2E") != "1", reason="set JSON_PRETTY_DIFF_E2E=1"
)


def _run(*args: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if len(value) < 32767}
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [str(arg) for arg in args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        env=env,
        check=False,
    )


def test_built_wheel_installs_and_runs(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    wheel = next(dist.glob("*.whl"))
    sdist = next(dist.glob("*.tar.gz"))

    names = zipfile.ZipFile(wheel).namelist()
    for module in (
        "py.typed",
        "infrastructure/_io.py",
        "infrastructure/_decode.py",
        "infrastructure/_output.py",
        "domain/_equality.py",
        "presentation/html_renderer/_matching.py",
        "presentation/html_renderer/_styles.py",
    ):
        assert f"json_pretty_diff/{module}" in names
    assert not [name for name in names if name.startswith("tests/")]
    with tarfile.open(sdist) as archive:
        members = archive.getnames()
    assert not [name for name in members if "tests/upstream/rfc" in name]
    for needed in (
        "tests/conftest.py",
        "tests/golden/report-1.1.1.html",
        "GUIDE.md",
        "CHANGELOG.md",
    ):
        assert [name for name in members if name.endswith(needed)], needed
    assert not [name for name in members if "__pycache__" in name or name.endswith(".pyc")]
    for notes in ("IMPROVEMENTS-round.md", "CERT-1.0-REPORT.md"):
        assert not [name for name in members if name.endswith(notes)]

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bin_dir = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bin_dir / "python"
    installed = _run(python, "-m", "pip", "install", "--no-index", "--no-deps", wheel)
    assert installed.returncode == 0, installed.stderr

    work = tmp_path / "work"
    work.mkdir()
    jpd = bin_dir / "jpd"
    version = _run(jpd, "--version", cwd=work)
    assert version.stdout.strip() == f"jpd {json_pretty_diff.__version__}"
    report = work / "out" / "diff.html"
    result = _run(jpd, FIXTURES / "base.json", FIXTURES / "update.json", "-o", report, cwd=work)
    assert result.returncode == 1, result.stderr
    assert "Report saved to" in result.stdout
    assert "Javier Lianes García" in report.read_text(encoding="utf-8")
    same = _run(jpd, FIXTURES / "base.json", FIXTURES / "base.json", cwd=work)
    assert same.returncode == 0 and same.stdout.startswith("<!DOCTYPE html>")
