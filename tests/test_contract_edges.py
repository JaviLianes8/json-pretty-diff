"""Edge contracts for input, warnings, output and line matching, one behaviour each."""

from __future__ import annotations

import errno
import io
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pytest
from conftest import FIXTURES, run_cli, write_bytes

from json_pretty_diff import compute_top_level_diff
from json_pretty_diff.application.use_cases import DiffUseCase
from json_pretty_diff.domain._equality import json_equal
from json_pretty_diff.infrastructure import _output
from json_pretty_diff.infrastructure._decode import decode_json
from json_pretty_diff.infrastructure._io import InputOutputError, load_json_object, shown_path
from json_pretty_diff.presentation.html_renderer._matching import line_opcodes, plain_opcodes

BASE = FIXTURES / "base.json"
UPDATE = FIXTURES / "update.json"
Capture = pytest.CaptureFixture[str]
REPEATS = "repeats names inside an object, the last value is used (RFC 8259 section 4): "


def test_the_same_nan_object_equals_itself() -> None:
    nan = float("nan")
    assert json_equal(nan, nan) is True
    assert not compute_top_level_diff({"a": nan}, {"a": nan}).has_differences


def test_paths_are_cut_in_the_nested_too_deeply_message(
    capsys: Capture, monkeypatch: pytest.MonkeyPatch
) -> None:
    def deep(self: DiffUseCase, source: Any, target: Any) -> Any:
        raise RecursionError

    monkeypatch.setattr(DiffUseCase, "execute", deep)
    # "." segments keep the file the same while the argument grows past the 200-character cut.
    source = str(FIXTURES) + "/." * 150 + "/base.json"
    assert run_cli(source, UPDATE) == 2
    err = capsys.readouterr().err
    assert err == f"Error: {source[:200]}... or {UPDATE} is nested too deeply to compare.\n"


def test_a_name_of_exactly_forty_characters_is_not_cut() -> None:
    name = "k" * 38  # quoted by json.dumps it is exactly 40 characters long
    note = decode_json(f'{{"{name}": 1, "{name}": 2}}')[1][0]
    assert note == REPEATS + '"' + name + '"'


def test_a_path_of_exactly_two_hundred_characters_is_not_cut() -> None:
    assert shown_path("p" * 200) == "p" * 200
    assert shown_path("p" * 201) == "p" * 200 + "..."


def test_big_endian_utf32_input_gets_the_utf32_hint(tmp_path: Path, capsys: Capture) -> None:
    text = b"\x00\x00\xfe\xff" + '{"a": 2}'.encode("utf-32-be")
    assert run_cli(write_bytes(tmp_path / "u.json", text), BASE) == 2
    assert capsys.readouterr().err.endswith("(it looks like UTF-32)\n")


def test_any_read_failure_carries_the_system_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_bytes(tmp_path / "a.json", b"{}")

    def fail(self: Path) -> bytes:
        raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(Path, "read_bytes", fail)
    with pytest.raises(InputOutputError, match=r"^Cannot read .*a\.json: Input/output error$"):
        load_json_object(path)


class _NoDescriptor:
    """A standard output replacement that has no file descriptor at all."""

    def write(self, text: str) -> int:
        return len(text)


def _closed() -> io.StringIO:
    stream = io.StringIO()
    stream.close()
    return stream


@pytest.mark.parametrize("make", [_NoDescriptor, _closed])
def test_discarding_a_stdout_without_a_descriptor_is_quiet(
    make: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdout", make())
    _output._discard_stdout()


def _difflib(old: list[str], new: list[str]) -> list[Any]:
    return list(SequenceMatcher(None, old, new).get_opcodes())


def test_a_budget_equal_to_the_steps_needed_gives_difflibs_result() -> None:
    # One scan of old: one step per line plus one per position of that line in new: 1 + 2.
    old, new = ["c", "a"], ["a", "b", "b"]
    assert line_opcodes(old, new, budget=3) == _difflib(old, new)


def test_a_budget_one_step_short_gives_the_plain_replacement() -> None:
    old, new = ["c", "a"], ["a", "b", "b"]
    assert _difflib(old, new) != plain_opcodes(old, new)
    assert line_opcodes(old, new, budget=2) == plain_opcodes(old, new)


def test_a_partial_scan_costs_only_the_lines_it_scans() -> None:
    old, new = list("abaca"), list("babc")
    assert _difflib(old, new) != plain_opcodes(old, new)
    assert line_opcodes(old, new, budget=17) == _difflib(old, new)
