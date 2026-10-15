"""Comparison rules kept on purpose in 1.2.0, pinned through the command line."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import run_cli, write_bytes

Capture = pytest.CaptureFixture[str]


@pytest.mark.parametrize(
    ("left", "right", "code"),
    [
        (b"1", b"1.0", 0),
        (b"1", b"1e0", 0),
        (b"0.1", b"0.10000000000000001", 0),
        (b"1", b"1.0000000000000001", 0),
        (b"-0", b"0", 0),
        (b"0.1", b"0.2", 1),
        (b"true", b"1", 1),
        (b"false", b"0", 1),
        (b"null", b"0", 1),
        (b'"1"', b"1", 1),
        (b"NaN", b"NaN", 0),
        (b"[1, true]", b"[1.0, true]", 0),
        (b"[1, true]", b"[1, 1]", 1),
    ],
)
def test_values_compare_as_documented(
    left: bytes, right: bytes, code: int, tmp_path: Path, capsys: Capture
) -> None:
    source = write_bytes(tmp_path / "s.json", b'{"k": ' + left + b"}")
    target = write_bytes(tmp_path / "t.json", b'{"k": ' + right + b"}")
    assert run_cli(source, target, "-q") == code
    assert run_cli(target, source, "-q") == code
