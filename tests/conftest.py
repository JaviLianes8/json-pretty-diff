"""Shared helpers: the pinned sources, small JSON files and a command-line runner."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from json_pretty_diff.cli import JsonPrettyDiffCLI

HERE = Path(__file__).parent
UPSTREAM = HERE / "upstream"
FIXTURES = HERE / "fixtures"
GOLDEN = HERE / "golden"
ROOT = HERE.parent
_TIMESTAMP = re.compile(r"Generated on \d{4}-\d\d-\d\d \d\d:\d\d:\d\d UTC")


def upstream(name: str) -> str:
    """Return a pinned source fetched by scripts/fetch_upstream.py, or skip the test."""
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} not fetched; run python scripts/fetch_upstream.py")
    return path.read_text(encoding="utf-8")


def normalize(report: str) -> str:
    """Replace the generation time, the only part of a report that changes between runs."""
    return _TIMESTAMP.sub("Generated on TIMESTAMP", report)


def fixture(name: str) -> Any:
    """Decode one of the JSON files in tests/fixtures."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> Path:
    """Write ``data`` as a JSON file and return its path."""
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def write_bytes(path: Path, data: bytes) -> Path:
    """Write raw bytes, for inputs that are not valid JSON or not UTF-8."""
    path.write_bytes(data)
    return path


def run_cli(*argv: str | Path) -> int:
    """Run the command line in process and return its exit code, errors included."""
    try:
        return JsonPrettyDiffCLI().run([str(arg) for arg in argv])
    except SystemExit as error:
        return int(error.code or 0)
