"""Section anchors: safe characters, and every anchor in a report is different."""

from __future__ import annotations

import re

import pytest

from json_pretty_diff.domain.services import compute_top_level_diff
from json_pretty_diff.presentation.html_renderer import render_html
from json_pretty_diff.presentation.html_renderer._anchors import sanitize_anchor


def anchors(*keys: str) -> list[str]:
    used: dict[str, int] = {}
    return [sanitize_anchor(key, used) for key in keys]


def test_non_alphanumeric_characters_become_dashes_and_ends_are_trimmed() -> None:
    assert anchors("a b.c", "  x  ", "ñandú 2") == ["a-b-c", "x", "ñandú-2"]


def test_a_key_with_no_letters_or_digits_becomes_key() -> None:
    assert anchors("", "---", "!") == ["key", "key-2", "key-3"]


def test_repeated_bases_are_numbered_from_two() -> None:
    assert anchors("a b", "a.b", "a/b") == ["a-b", "a-b-2", "a-b-3"]


@pytest.mark.parametrize(
    "keys",
    [
        ("a b", "a-b", "a-b-2"),
        ("a-b-2", "a b", "a-b"),
        ("a b", "a-b", "a-b-2", "a.b-2", "a-b-2-2"),
        ("x", "x-2", "x 2", "x", "x-3"),
    ],
)
def test_anchors_never_repeat(keys: tuple[str, ...]) -> None:
    result = anchors(*keys)
    assert len(set(result)) == len(result)


def test_numbered_anchor_skips_a_plain_anchor_already_taken() -> None:
    assert anchors("a-b-2", "a b", "a-b") == ["a-b-2", "a-b", "a-b-3"]
    assert anchors("a b", "a-b", "a-b-2") == ["a-b", "a-b-2", "a-b-2-2"]


def test_report_ids_are_unique_and_links_match_them() -> None:
    report = render_html(compute_top_level_diff({}, {"a b": 1, "a-b": 2, "a-b-2": 3}))
    ids = re.findall(r'<section id="diff-([^"]+)"', report)
    assert len(ids) == 3 and len(set(ids)) == 3
    links = re.findall(r'<a href="#diff-([^"]+)"', report)
    assert sorted(links) == sorted(ids)
    for key, anchor in zip(["a b", "a-b", "a-b-2"], ids):
        section = report[report.index(f'id="diff-{anchor}"') :]
        assert section.index(f"<code>{key}</code>") < section.index("</section>")


def test_numbered_anchor_skips_every_number_already_taken() -> None:
    assert anchors("a-b-2", "a-b-3", "a b", "a.b") == ["a-b-2", "a-b-3", "a-b", "a-b-4"]
