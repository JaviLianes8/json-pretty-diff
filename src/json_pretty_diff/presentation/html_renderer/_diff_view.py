"""HTML generation helpers for diff sections."""

from __future__ import annotations

import html
from typing import Any, Dict, Iterable, List

from ._diff_data import diff_lines, prepare_serialized_for_diff

def render_diff_lines(lines: Iterable[str], truncated: bool) -> str:
    """Turns diff lines into HTML spans with contextual classes."""

    rendered: List[str] = []
    for line in lines:
        escaped = html.escape(line)
        if line.startswith("@@"):
            css_class = "hunk"
        elif line.startswith("+++") or line.startswith("---"):
            css_class = "ctx"
        elif line.startswith("+"):
            css_class = "add"
        elif line.startswith("-"):
            css_class = "del"
        else:
            css_class = "ctx"
        rendered.append(f'<span class="{css_class}">{escaped}</span>')

    if truncated:
        rendered.append('<span class="ctx">… (truncated)</span>')

    return "\n".join(rendered)


def render_truncated_details(
    old_full: str | None, new_full: str | None, status: str
) -> str:
    """Renders expandable panels containing full values when truncated."""

    if old_full is None and new_full is None and status != "removed":
        return ""

    status_classes = {
        "added": "truncated-new truncated-new--added",
        "changed": "truncated-new truncated-new--changed",
        "removed": "truncated-new truncated-new--removed",
    }

    columns: List[str] = []
    if old_full is not None:
        columns.append(
            "".join(
                [
                    '<div class="truncated-column">',
                    '<h4 class="truncated-title">Old value</h4>',
                    f'<pre>{html.escape(old_full)}</pre>',
                    "</div>",
                ]
            )
        )

    new_column_class = status_classes.get(status, "truncated-new")
    if new_full is not None:
        columns.append(
            "".join(
                [
                    f'<div class="truncated-column {new_column_class}">',
                    '<h4 class="truncated-title">New value</h4>',
                    f'<pre>{html.escape(new_full)}</pre>',
                    "</div>",
                ]
            )
        )
    elif status == "removed":
        columns.append(
            "".join(
                [
                    f'<div class="truncated-column {new_column_class}">',
                    '<h4 class="truncated-title">New value</h4>',
                    '<pre>No new value (entry removed).</pre>',
                    "</div>",
                ]
            )
        )

    if not columns:
        return ""

    return "".join(
        [
            '<details class="truncated-details">',
            '<summary>Show full content</summary>',
            '<div class="truncated-wrapper">',
            "".join(columns),
            "</div>",
            "</details>",
        ]
    )

def render_diff_section(entry: Dict[str, Any]) -> str:
    """Renders the HTML section containing the formatted diff for one key."""

    key = entry["key"]
    anchor = entry["anchor"]
    status = entry["status"]

    old_serialized, truncated_old, old_full = prepare_serialized_for_diff(entry["old"])
    new_serialized, truncated_new, new_full = prepare_serialized_for_diff(entry["new"])

    old_lines = old_serialized.splitlines(keepends=True)
    new_lines = new_serialized.splitlines(keepends=True)
    diff_result = diff_lines(old_lines, new_lines)
    cleaned_lines = list(diff_result)
    if len(cleaned_lines) >= 2 and cleaned_lines[0].startswith("---") and cleaned_lines[1].startswith("+++"):
        cleaned_lines = cleaned_lines[2:]

    diff_html = render_diff_lines(cleaned_lines, truncated_old or truncated_new)

    truncated_panel = ""
    if truncated_old or truncated_new:
        truncated_panel = render_truncated_details(
            old_full if truncated_old else None,
            new_full if truncated_new else None,
            status,
        )

    section_parts = [
        f'<section id="diff-{anchor}" class="gitdiff-block {status}">',
        f"<h3><code>{html.escape(key)}</code></h3>",
        f'<pre class="gitdiff">{diff_html}</pre>',
    ]

    if truncated_panel:
        section_parts.append(truncated_panel)

    section_parts.append("</section>")

    return "\n".join(section_parts)

def render_git_sections(entries: List[Dict[str, Any]]) -> str:
    """Renders the diff sections for the provided entries."""

    if not entries:
        return ""

    parts: List[str] = [
        '<section class="gitdiff-container page-section">',
        '<details class="panel-toggle diff-toggle" open>',
        '<summary>DIFF</summary>',
        '<div class="gitdiff-body">',
        '<pre class="gitdiff gitdiff-legend">',
        '<span class="ctx">--- old</span>',
        '<span class="ctx">+++ new</span>',
        '</pre>',
    ]

    parts.extend(render_diff_section(entry) for entry in entries)
    parts.extend(['</div>', '</details>', '</section>'])
    return "\n".join(parts)

__all__ = [
    "render_diff_lines",
    "render_diff_section",
    "render_git_sections",
    "render_truncated_details",
]
