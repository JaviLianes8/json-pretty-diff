"""Edge contracts for the rendered page, one behaviour each."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import FIXTURES

from json_pretty_diff import DiffResult, compute_top_level_diff, render_html
from json_pretty_diff.presentation.html_renderer._full_json_script import (
    render_full_json_filter_script,
)

BASE = FIXTURES / "base.json"
UPDATE = FIXTURES / "update.json"
Capture = pytest.CaptureFixture[str]
REPEATS = "repeats names inside an object, the last value is used (RFC 8259 section 4): "


def _section(page: str, key: str) -> str:
    section = page[page.index(f'<section id="diff-{key}"') :]
    return section[: section.index("</section>")]


def test_a_removed_long_value_marks_its_placeholder_column_as_removed() -> None:
    section = _section(render_html(compute_top_level_diff({"k": "x" * 10_001}, {})), "k")
    assert '<div class="truncated-column truncated-new truncated-new--removed">' in section


def test_the_full_old_value_is_escaped() -> None:
    page = render_html(compute_top_level_diff({"k": "<b>" + "x" * 10_001}, {"k": 1}))
    assert "<b>" not in page and _section(page, "k").count("&quot;&lt;b&gt;") == 2


def test_the_full_new_value_is_escaped() -> None:
    page = render_html(compute_top_level_diff({"k": 1}, {"k": "<b>" + "x" * 10_001}))
    assert "<b>" not in page and _section(page, "k").count("&quot;&lt;b&gt;") == 2


def test_a_long_new_value_alone_marks_the_diff_as_truncated() -> None:
    page = render_html(compute_top_level_diff({"k": "short"}, {"k": "y" * 10_001}))
    assert "… (truncated)" in _section(page, "k")


def test_an_empty_new_cell_holds_a_non_breaking_space() -> None:
    page = render_html(compute_top_level_diff({"a": {"w": 0, "x": 1}}, {"a": {"x": 1}}))
    assert '<td class="code-cell diff-removed"><pre>&nbsp;</pre></td>' in page


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_clearing_the_search_puts_the_text_back_escaped(tmp_path: Path) -> None:
    script = render_full_json_filter_script("t")
    start = script.index("    function escapeHtml(")
    body = script[start : script.index("    function ensureMatchVisible(")]
    code = body + "console.log(JSON.stringify(highlightText('\"<b>&</b>\"', '')));"
    (tmp_path / "s.js").write_text(code, encoding="utf-8")
    out = subprocess.run(
        ["node", str(tmp_path / "s.js")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert json.loads(out.stdout) == "&quot;&lt;b&gt;&amp;&lt;/b&gt;&quot;"


def test_carriage_returns_in_names_are_kept() -> None:
    page = render_html(compute_top_level_diff({"a\rb": 1}, {}))
    assert "a\rb" in page and "\\u000d" not in page


def test_unit_separator_in_names_is_escaped() -> None:
    page = render_html(compute_top_level_diff({"a\x1fb": 1}, {}))
    assert "\x1f" not in page and "a\\u001fb" in page


def test_anchors_are_handed_out_added_first_then_removed_then_changed() -> None:
    page = render_html(compute_top_level_diff({"a-b": 1, "a+b": 1}, {"a-b": 2, "a b": 1}))
    assert '<section id="diff-a-b" class="gitdiff-block added">' in page
    assert '<section id="diff-a-b-2" class="gitdiff-block removed">' in page
    assert '<section id="diff-a-b-3" class="gitdiff-block changed">' in page


def test_added_and_removed_names_are_escaped_in_the_summary() -> None:
    page = render_html(compute_top_level_diff({"<i>": 1}, {"<u>": 1}))
    assert "<i>" not in page and "<u>" not in page
    assert "<code>&lt;i&gt;</code></a></li>" in page
    assert "<code>&lt;u&gt;</code></a></li>" in page


def test_changed_summary_links_are_sorted_even_for_a_hand_built_result() -> None:
    changed = {"b": {"old": 1, "new": 2}, "a": {"old": 1, "new": 2}}
    page = render_html(DiffResult(changed=changed), include_timestamp=False)
    first = page.index('<span class="change-key"><code>a</code>')
    assert first < page.index('<span class="change-key"><code>b</code>')


def test_changed_sections_are_sorted_even_for_a_hand_built_result() -> None:
    changed = {"b": {"old": 1, "new": 2}, "a": {"old": 1, "new": 2}}
    page = render_html(DiffResult(changed=changed), include_timestamp=False)
    assert page.index('<section id="diff-a"') < page.index('<section id="diff-b"')
