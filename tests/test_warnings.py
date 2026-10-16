"""Warnings: NaN and Infinity, numbers beyond a double, repeated names (RFC 8259 sections 4, 6)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from conftest import FIXTURES, run_cli, write_bytes

from json_pretty_diff import compute_top_level_diff, render_html
from json_pretty_diff.infrastructure._decode import decode_json
from json_pretty_diff.infrastructure._io import load_json_object

BASE = FIXTURES / "base.json"
Capture = pytest.CaptureFixture[str]
CONSTANTS = "holds values RFC 8259 does not allow (section 6), read and compared as numbers: "
OVERFLOW = "holds numbers beyond the range of a double, read and compared as infinity: "
REPEATS = "repeats names inside an object, the last value is used (RFC 8259 section 4): "


def test_clean_text_has_no_notes_and_decodes_like_json_loads() -> None:
    assert decode_json('{"a": [1, 2.5, -0.0, 1e300, "x", null, true]}') == (
        {"a": [1, 2.5, -0.0, 1e300, "x", None, True]},
        [],
    )


def test_nan_and_infinities_are_read_as_floats_and_named_once_in_order() -> None:
    data, notes = decode_json('{"a": [NaN, Infinity, -Infinity, NaN, Infinity]}')
    assert str(data["a"]) == "[nan, inf, -inf, nan, inf]"
    assert notes == [CONSTANTS + "NaN, Infinity, -Infinity"]


@pytest.mark.parametrize("text", ["1e400", "-1e400", "1.5e309", "1" + "0" * 400 + ".0"])
def test_a_number_beyond_a_double_is_infinity_with_a_note(text: str) -> None:
    data, notes = decode_json(f'{{"a": {text}}}')
    assert data["a"] == (float("-inf") if text.startswith("-") else float("inf"))
    shown = text if len(text) <= 40 else text[:40] + "..."
    assert notes == [OVERFLOW + shown]


def test_the_largest_double_and_big_integers_are_not_overflows() -> None:
    assert decode_json('{"a": 1.7976931348623157e308, "b": 1' + "0" * 400 + "}")[1] == []


def test_repeated_names_keep_the_last_value_and_its_first_position() -> None:
    data, notes = decode_json('{"a": 1, "b": 2, "a": 3, "c": {"x": 1, "x": 2}}')
    assert data == {"a": 3, "b": 2, "c": {"x": 2}}
    assert list(data) == ["a", "b", "c"]
    assert notes == [REPEATS + '"x", "a"']


def test_a_name_repeated_in_two_objects_is_listed_once() -> None:
    notes = decode_json('{"a": {"k": 1, "k": 1}, "b": {"k": 2, "k": 2}}')[1]
    assert notes == [REPEATS + '"k"']


def test_five_examples_are_shown_and_the_rest_counted() -> None:
    names = [f"n{i}" for i in range(8)]
    text = "{" + ", ".join(f'"{name}": 1, "{name}": 2' for name in names) + "}"
    assert decode_json(text)[1] == [REPEATS + '"n0", "n1", "n2", "n3", "n4" and 3 more']


def test_long_names_are_cut_in_the_message() -> None:
    name = "k" * 500
    note = decode_json(f'{{"{name}": 1, "{name}": 2}}')[1][0]
    assert note == REPEATS + '"' + "k" * 39 + "..."
    assert len(note) < 200


def test_notes_come_in_a_fixed_order() -> None:
    notes = decode_json('{"a": 1, "a": 1e999, "b": NaN}')[1]
    assert [note.split(" ", 1)[0] for note in notes] == ["holds", "holds", "repeats"]
    assert notes[0].startswith(CONSTANTS) and notes[1].startswith(OVERFLOW)


def test_the_loader_prefixes_each_note_with_the_path(tmp_path: Path) -> None:
    path = write_bytes(tmp_path / "w.json", b'{"a": NaN, "a": 1}')
    warnings: list[str] = []
    assert load_json_object(path, warnings) == {"a": 1}
    assert warnings == [f"{path} {CONSTANTS}NaN", f"{path} {REPEATS}" + '"a"']
    assert load_json_object(path) == {"a": 1}


def test_the_command_prints_warnings_and_keeps_the_exit_code(
    tmp_path: Path, capsys: Capture
) -> None:
    source = write_bytes(tmp_path / "s.json", b'{"a": NaN}')
    target = write_bytes(tmp_path / "t.json", b'{"a": NaN, "b": 1e400}')
    report = tmp_path / "r.html"
    assert run_cli(source, source, "-o", report) == 0
    assert capsys.readouterr().err == f"Warning: {source} {CONSTANTS}NaN\n"
    assert run_cli(source, target, "-o", report) == 1
    captured = capsys.readouterr()
    assert captured.err == (
        f"Warning: {source} {CONSTANTS}NaN\n"
        f"Warning: {target} {CONSTANTS}NaN\n"
        f"Warning: {target} {OVERFLOW}1e400\n"
    )
    assert captured.out.startswith("Report saved to ")
    page = report.read_text(encoding="utf-8")
    items = re.findall(r"<li>([^<]*)</li>", page[page.index("<h2>Warnings</h2>") :])
    assert items[:3] == [line[len("Warning: ") :] for line in captured.err.splitlines()]


def test_quiet_silences_warnings_but_the_report_keeps_them(tmp_path: Path, capsys: Capture) -> None:
    source = write_bytes(tmp_path / "s.json", b'{"a": 1, "a": 2}')
    report = tmp_path / "r.html"
    assert run_cli(source, BASE, "-q", "-o", report) == 1
    assert capsys.readouterr() == ("", "")
    assert "<h2>Warnings</h2>" in report.read_text(encoding="utf-8")


def test_warnings_go_to_stderr_when_the_report_goes_to_stdout(
    tmp_path: Path, capsys: Capture
) -> None:
    source = write_bytes(tmp_path / "s.json", b'{"a": Infinity}')
    assert run_cli(source, source) == 0
    captured = capsys.readouterr()
    assert captured.err == f"Warning: {source} {CONSTANTS}Infinity\n"
    assert captured.out.startswith("<!DOCTYPE html>") and "<h2>Warnings</h2>" in captured.out


def test_warning_section_is_escaped_and_absent_without_warnings() -> None:
    diff = compute_top_level_diff({}, {})
    assert "Warnings" not in render_html(diff)
    page = render_html(diff, warnings=["<b>x</b> & y"])
    assert '<ul class="warnings-list"><li>&lt;b&gt;x&lt;/b&gt; &amp; y</li></ul>' in page
    assert '<section class="warnings page-section" style="' in page
    plain = render_html(diff, warnings=["w"], include_styles=False)
    assert '<section class="warnings page-section">' in plain
    assert page.index("<h2>Warnings</h2>") < page.index('<section class="summary-panel')


def test_a_lone_surrogate_name_in_a_warning_does_not_crash(tmp_path: Path, capsys: Capture) -> None:
    source = write_bytes(tmp_path / "s.json", b'{"\\ud800": 1, "\\ud800": 2}')
    report = tmp_path / "r.html"
    assert run_cli(source, source, "-o", report) == 0
    assert "Warning: " in capsys.readouterr().err
    assert "\\ud800" in report.read_text(encoding="utf-8")


def test_names_keep_their_characters_in_the_message() -> None:
    assert decode_json('{"café": 1, "café": 2}')[1] == [REPEATS + '"café"']
