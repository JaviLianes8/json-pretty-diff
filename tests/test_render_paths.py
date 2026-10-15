"""Less common rendering paths: the full JSON table and hand-built diff results."""

from __future__ import annotations

import re
import sys

import pytest

from json_pretty_diff import cli
from json_pretty_diff.domain.models import DiffResult
from json_pretty_diff.domain.services import compute_top_level_diff
from json_pretty_diff.presentation.html_renderer import render_html
from json_pretty_diff.presentation.html_renderer._diff_data import split_lines
from json_pretty_diff.presentation.html_renderer._diff_view import render_diff_lines


def _right_cells(report: str) -> list[str]:
    return re.findall(r'<td class="code-cell (\S+)"><pre>', report)[1::2]


def test_full_json_marks_inserted_removed_and_modified_lines() -> None:
    report = render_html(compute_top_level_diff({"a": 1, "b": 2}, {"a": 1, "b": 3, "c": 4}))
    assert set(_right_cells(report)) >= {"neutral", "diff-modified"}
    small: dict[str, object] = {"a": {"x": 1}, "b": 1}
    large: dict[str, object] = {"a": {"w": 0, "x": 1}, "b": 1}
    assert "diff-added" in _right_cells(render_html(compute_top_level_diff(small, large)))
    assert "diff-removed" in _right_cells(render_html(compute_top_level_diff(large, small)))


def test_empty_cells_hold_a_non_breaking_space() -> None:
    report = render_html(compute_top_level_diff({"a": {"x": 1}}, {"a": {"w": 0, "x": 1}}))
    assert '<td class="code-cell left"><pre>&nbsp;</pre></td>' in report


def test_values_json_cannot_encode_fall_back_to_repr() -> None:
    diff = DiffResult(changed={"k": {"old": {1, 2}, "new": 1}}, source_snapshot={"k": {1, 2}})
    report = render_html(diff)
    assert "{1, 2}" in report


def test_a_key_listed_twice_gets_one_anchor() -> None:
    diff = DiffResult(added=["k"], changed={"k": {"old": 1, "new": 2}}, added_values={"k": 2})
    ids = re.findall(r'<section id="diff-([^"]+)"', render_html(diff))
    assert ids == ["k", "k"]


def test_console_entry_point_runs_the_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["jpd", "--version"])
    with pytest.raises(SystemExit) as raised:
        cli.main()
    assert raised.value.code == 0
    assert capsys.readouterr().out.startswith("jpd ")


def test_only_double_at_lines_are_hunk_headers() -> None:
    html = render_diff_lines(["@ x", "@@ -1 +1 @@"], False)
    assert re.findall(r'<span class="(\w+)">', html) == ["ctx", "hunk"]


def test_a_long_new_value_alone_gets_the_full_content_panel() -> None:
    report = render_html(compute_top_level_diff({"k": "short"}, {"k": "y" * 10_001}))
    assert '<details class="truncated-details">' in report
    assert "New value" in report and "Old value" not in report


@pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\x85"])
def test_unicode_line_separators_stay_inside_their_row(separator: str) -> None:
    value = f"x{separator}y"
    report = render_html(compute_top_level_diff({"a": value, "b": 1}, {"a": value, "b": 2}))
    assert (
        f'<td class="code-cell left"><pre>  &quot;a&quot;: &quot;x{separator}y&quot;,</pre>'
        in report
    )
    report = render_html(compute_top_level_diff({"a": value}, {"a": value + "!"}))
    assert f'<span class="del">-&quot;x{separator}y&quot;\n</span>' in report


def test_split_lines_breaks_at_newlines_only() -> None:
    assert split_lines("") == [] and split_lines("a\n") == ["a"]
    assert split_lines("a\u2028b\nc") == ["a\u2028b", "c"]
    assert split_lines("a\nb", keepends=True) == ["a\n", "b"]
    assert split_lines("a\nb\n", keepends=True) == ["a\n", "b\n"]
