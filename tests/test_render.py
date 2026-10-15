"""The HTML report: the 1.1.1 layout is pinned and every piece taken from input is escaped."""

from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest
from conftest import GOLDEN, fixture, normalize

from json_pretty_diff import __version__
from json_pretty_diff.domain.services import compute_top_level_diff
from json_pretty_diff.presentation.html_renderer import render_html
from json_pretty_diff.presentation.html_renderer._diff_data import (
    MISSING,
    prepare_serialized_for_diff,
    serialize_for_diff,
    truncate_text,
)
from json_pretty_diff.presentation.html_renderer._diff_view import (
    render_diff_lines,
    render_git_sections,
    render_truncated_details,
)

LONG = "x" * 10_001


@pytest.mark.parametrize(
    ("golden", "update", "styles"),
    [
        ("report-1.1.1.html", "update.json", True),
        ("report-1.1.1-no-style.html", "update.json", False),
        ("report-1.1.1-same.html", "base.json", True),
    ],
)
def test_report_is_byte_identical_to_version_1_1_1(golden: str, update: str, styles: bool) -> None:
    # The golden files were rendered by the 1.1.1 code before any change of this round.
    diff = compute_top_level_diff(fixture("base.json"), fixture(update))
    report = normalize(render_html(diff, include_styles=styles))
    assert report == (GOLDEN / golden).read_text(encoding="utf-8")


def test_header_carries_the_utc_time_and_version() -> None:
    before = datetime.now(timezone.utc).replace(microsecond=0)
    report = render_html(compute_top_level_diff({}, {"a": 1}))
    match = re.search(r"Generated on (\S+ \S+) UTC &mdash; v(\S+)</p>", report)
    assert match is not None
    stamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    assert before <= stamp <= datetime.now(timezone.utc)
    assert match.group(2) == __version__


def test_keys_and_values_from_the_input_are_escaped() -> None:
    hostile = "<script>alert('k')</script>"
    report = render_html(compute_top_level_diff({hostile: "<b>"}, {hostile: '"&"'}))
    assert "<script>alert" not in report
    assert "&lt;script&gt;alert(&#x27;k&#x27;)&lt;/script&gt;" in report
    assert "&lt;b&gt;" in report
    assert "&quot;\\&quot;&amp;\\&quot;&quot;" in report


def test_no_style_drops_only_the_stylesheet() -> None:
    diff = compute_top_level_diff({"a": 1}, {"a": 2})
    styled = normalize(render_html(diff))
    plain = normalize(render_html(diff, include_styles=False))
    assert "<style>" in styled and "<style>" not in plain
    start, end = styled.index("<style>"), styled.index("</style>") + len("</style>")
    assert styled[:start] + styled[end:] == plain


def test_empty_documents_have_no_diff_or_full_json_section() -> None:
    report = render_html(compute_top_level_diff({}, {}), include_styles=False)
    assert "No differences." in report
    assert "gitdiff-container" not in report
    assert "full-json" not in report
    assert "<script>" not in report


def test_full_json_is_shown_when_one_side_has_content() -> None:
    report = render_html(compute_top_level_diff({}, {"a": 1}))
    assert '<table id="full-json-table"' in report
    assert 'data-json-target="full-json-table"' in report
    assert "document.getElementById('full-json-table')" in report


def test_long_values_are_truncated_with_a_full_content_panel() -> None:
    report = render_html(compute_top_level_diff({"k": LONG}, {"k": "short"}))
    section = report[report.index('<section id="diff-k"') :]
    section = section[: section.index("</section>")]
    assert "… (truncated)" in section
    assert '<details class="truncated-details">' in section
    assert "Old value" in section and "New value" not in section
    assert section.count(LONG) == 1


def test_removed_long_value_says_there_is_no_new_value() -> None:
    report = render_html(compute_top_level_diff({"k": LONG}, {}))
    assert "No new value (entry removed)." in report
    assert "truncated-new--removed" in report


def test_added_long_value_shows_the_new_value_only() -> None:
    panel = render_truncated_details(None, "full", "added")
    assert "truncated-new--added" in panel and "Old value" not in panel
    assert render_truncated_details(None, None, "added") == ""
    assert render_truncated_details(None, None, "changed") == ""
    assert "truncated-new truncated-new--changed" in render_truncated_details("a", "b", "changed")
    assert 'class="truncated-column truncated-new">' in render_truncated_details(None, "b", "x")


def test_truncation_limit_is_ten_thousand_characters() -> None:
    assert truncate_text("x" * 10_000) == ("x" * 10_000, False)
    assert truncate_text(LONG) == ("x" * 10_000, True)
    assert truncate_text("abcdef", limit=3) == ("abc", True)


def test_serialization_is_sorted_indented_and_falls_back_to_repr() -> None:
    assert serialize_for_diff({"b": 1, "a": "ñ"}) == '{\n  "a": "ñ",\n  "b": 1\n}'
    assert serialize_for_diff({1, 2}) == "{1, 2}"
    assert prepare_serialized_for_diff(MISSING) == ("", False, "")
    assert prepare_serialized_for_diff(LONG)[1] is True


def test_diff_lines_get_a_class_by_their_prefix() -> None:
    html = render_diff_lines(["@@ -1 +1 @@", "--- old", "+++ new", "+a", "-b", " c"], False)
    classes = re.findall(r'<span class="(\w+)">', html)
    assert classes == ["hunk", "ctx", "ctx", "add", "del", "ctx"]
    assert "(truncated)" in render_diff_lines([], True)
    assert render_diff_lines(["+<a>"], False) == '<span class="add">+&lt;a&gt;</span>'


def test_diff_sections_follow_added_removed_changed_order() -> None:
    report = render_html(compute_top_level_diff({"r": 1, "c": 1}, {"c": 2, "a": 1}))
    order = re.findall(r'<section id="diff-(\w+)" class="gitdiff-block (\w+)">', report)
    assert order == [("a", "added"), ("r", "removed"), ("c", "changed")]
    assert render_git_sections([]) == ""


def test_summary_counts_and_links() -> None:
    report = render_html(compute_top_level_diff({"r": 1, "c": 1}, {"c": 2, "a": 1, "b": 2}))
    assert "Added: 2&nbsp;·&nbsp;Removed: 1&nbsp;·&nbsp;Changed: 1" in report
    assert '<a href="#diff-c" class="change-link">' in report
    assert '<li><a href="#diff-a"><code>a</code></a></li>' in report
    assert report.count('<p class="empty">No entries.</p>') == 0
    assert "No differences." not in report


def test_bool_and_number_change_is_rendered() -> None:
    report = render_html(compute_top_level_diff({"flag": True}, {"flag": 1}))
    assert '<span class="del">-true</span>' in report
    assert '<span class="add">+1</span>' in report
