"""Seeded fuzzing: any input ends in a report or a documented error, never a traceback."""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any

import pytest
from conftest import FIXTURES, run_cli, write_bytes

from json_pretty_diff import compute_top_level_diff, render_html
from json_pretty_diff.infrastructure._io import InputOutputError, load_json_object

Capture = pytest.CaptureFixture[str]
_ATOMS: list[Any] = [
    0,
    1,
    -1,
    1.0,
    0.5,
    1e300,
    float("nan"),
    float("inf"),
    True,
    False,
    None,
    "",
    "é",
    " ",
    "<b>&",
    "\ud800",
    "a\nb",
    10**30,
]


def _value(rng: random.Random, depth: int) -> Any:
    roll = rng.random()
    if depth <= 0 or roll < 0.4:
        return rng.choice(_ATOMS)
    if roll < 0.7:
        return [_value(rng, depth - 1) for _ in range(rng.randrange(4))]
    return {rng.choice(["a", "b", "", "<k>", "a b"]): _value(rng, depth - 1) for _ in range(3)}


def _document(rng: random.Random) -> dict[str, Any]:
    return {rng.choice("abcdefgh"): _value(rng, 3) for _ in range(rng.randrange(6))}


def test_random_documents_render_and_compare_like_themselves() -> None:
    rng = random.Random(20261015)
    for _ in range(300):
        source, target = _document(rng), _document(rng)
        page = render_html(compute_top_level_diff(source, target), include_timestamp=False)
        assert page.startswith("<!DOCTYPE html>") and page.endswith("</html>")
        assert not compute_top_level_diff(source, json.loads(json.dumps(source))).has_differences


def test_mutated_files_load_or_fail_with_the_documented_error(tmp_path: Path) -> None:
    rng = random.Random(6901)
    seed = (FIXTURES / "update.json").read_bytes()
    pieces = [b"NaN", b"-Infinity", b"1e999", b'"a": 1, "a"', b"\xff", b"\\ud800", b"[", b"}"]
    path = tmp_path / "m.json"
    outcomes = {"dict": 0, "error": 0}
    for _ in range(600):
        data = bytearray(seed)
        for _ in range(rng.randrange(1, 4)):
            at = rng.randrange(len(data) + 1)
            if rng.random() < 0.5:
                data[at:at] = rng.choice(pieces)
            else:
                del data[at : at + rng.randrange(1, 4)]
        path.write_bytes(bytes(data))
        warnings: list[str] = []
        try:
            loaded = load_json_object(path, warnings)
        except InputOutputError as error:
            assert len(str(error)) < len(str(path)) + 200
            outcomes["error"] += 1
        else:
            assert isinstance(loaded, dict)
            assert all(message.startswith(f"{path} ") for message in warnings)
            outcomes["dict"] += 1
    assert outcomes["dict"] > 30 and outcomes["error"] > 30


@pytest.mark.parametrize(
    "content",
    [b"", b" ", b"\x00", b"{" * 50_000, b'{"a": "' + b"x" * 2_000_000 + b'"}', b"\xef\xbb\xbf"],
    ids=["empty", "space", "nul", "open-braces", "long-string", "bom-only"],
)
def test_hostile_files_end_with_exit_two_or_a_report(
    tmp_path: Path, capsys: Capture, content: bytes
) -> None:
    path = write_bytes(tmp_path / "h.json", content)
    code = run_cli(path, FIXTURES / "base.json", "-q", "-o", tmp_path / "r.html")
    captured = capsys.readouterr()
    assert code in (1, 2)
    assert (code == 2) == captured.err.startswith("Error: ")
    assert len(captured.err) < 400


@pytest.mark.parametrize("make", ["keys", "duplicates", "nans"])
def test_time_grows_linearly_with_the_input(tmp_path: Path, make: str) -> None:
    def text(n: int) -> str:
        if make == "keys":
            return json.dumps({f"k{i}": [i, str(i)] for i in range(n)})
        if make == "duplicates":
            return "{" + ", ".join(f'"k{i % 50}": {i}' for i in range(n)) + "}"
        return "{" + ", ".join(f'"k{i}": NaN' for i in range(n)) + "}"

    def seconds(n: int) -> float:
        source = write_bytes(tmp_path / "s.json", text(n).encode())
        start = time.perf_counter()
        assert run_cli(source, FIXTURES / "base.json", "-q", "-o", tmp_path / "r.html") == 1
        return time.perf_counter() - start

    small, large = min(seconds(5_000) for _ in range(2)), min(seconds(40_000) for _ in range(2))
    assert large < max(small, 0.05) * 8 * 3
