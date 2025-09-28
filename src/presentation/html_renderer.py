"""HTML rendering utilities for JSON Pretty Diff."""
import html
import json
from difflib import SequenceMatcher, unified_diff
from typing import Any, Dict, Iterable, List, Tuple

from domain.models import DiffResult


_MISSING = object()


def _format_value(value: Any) -> str:
    """Returns an HTML-safe representation for a JSON value."""

    try:
        serialized = json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        serialized = repr(value)
    return html.escape(serialized)


def _serialize_for_diff(value: Any) -> str:
    """Serializes a JSON value for diff computation."""

    try:
        return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(value)


def _truncate_text(value: str, limit: int = 10_000) -> Tuple[str, bool]:
    """Truncates a string to the provided limit."""

    if len(value) <= limit:
        return value, False
    return value[:limit], True


def _prepare_serialized_for_diff(value: Any) -> Tuple[str, bool]:
    """Serializes and truncates a value for diff visualization."""

    if value is _MISSING:
        return "", False
    serialized = _serialize_for_diff(value)
    return _truncate_text(serialized)


def _diff_lines(old: Iterable[str], new: Iterable[str]) -> List[str]:
    """Builds a unified diff between two iterables of lines."""

    return list(
        unified_diff(
            list(old),
            list(new),
            fromfile="old",
            tofile="new",
            lineterm="",
        )
    )


def _sanitize_anchor(key: str, used: Dict[str, int]) -> str:
    """Creates a safe and unique anchor identifier for the given key."""

    base = "".join(ch if ch.isalnum() else "-" for ch in key).strip("-") or "key"
    index = used.get(base, 0)
    if index:
        anchor = f"{base}-{index + 1}"
    else:
        anchor = base
    used[base] = index + 1
    return anchor


def _render_diff_lines(lines: Iterable[str], truncated: bool) -> str:
    """Renders diff lines as HTML spans with contextual classes."""

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
        rendered.append('<span class="ctx">… (truncado)</span>')

    return "\n".join(rendered)


def _serialize_full_json(data: Any) -> str:
    """Serializes the full JSON payload preserving readability."""

    try:
        return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(data)


def _build_side_by_side_rows(old_lines: List[str], new_lines: List[str]) -> str:
    """Creates table rows highlighting line level differences."""

    matcher = SequenceMatcher(None, old_lines, new_lines)
    rows: List[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_chunk = old_lines[i1:i2]
        new_chunk = new_lines[j1:j2]
        limit = max(len(old_chunk), len(new_chunk)) or 1

        for index in range(limit):
            old_line = old_chunk[index] if index < len(old_chunk) else ""
            new_line = new_chunk[index] if index < len(new_chunk) else ""

            if tag == "equal":
                old_class = new_class = "ctx"
            elif tag == "replace":
                old_class = "del"
                new_class = "mix"
            elif tag == "delete":
                old_class = "del"
                new_class = "empty"
            elif tag == "insert":
                old_class = "empty"
                new_class = "mix"
            else:
                old_class = new_class = "ctx"

            old_cell = html.escape(old_line) if old_line else "&nbsp;"
            new_cell = html.escape(new_line) if new_line else "&nbsp;"

            rows.append(
                "".join(
                    [
                        "<tr>",
                        f'<td class="code-cell {old_class}"><pre>{old_cell}</pre></td>',
                        f'<td class="code-cell {new_class}"><pre>{new_cell}</pre></td>',
                        "</tr>",
                    ]
                )
            )

    return "\n".join(rows)


def _render_full_json_section(diff: DiffResult) -> str:
    """Renders the expandable section with the complete JSON snapshots."""

    if not diff.source_snapshot and not diff.target_snapshot:
        return ""

    old_serialized = _serialize_full_json(diff.source_snapshot)
    new_serialized = _serialize_full_json(diff.target_snapshot)

    old_lines = old_serialized.splitlines()
    new_lines = new_serialized.splitlines()
    table_rows = _build_side_by_side_rows(old_lines, new_lines)

    return "\n".join(
        [
            '<section class="full-json-section">',
            '<details class="full-json-details">',
            '<summary>See full JSON pretty print</summary>',
            '<div class="full-json-wrapper">',
            '<table class="full-json-table">',
            "<thead>",
            "<tr>",
            "<th>Old JSON pretty print</th>",
            "<th>New JSON pretty print</th>",
            "</tr>",
            "</thead>",
            "<tbody>",
            table_rows,
            "</tbody>",
            "</table>",
            "</div>",
            "</details>",
            "</section>",
        ]
    )


def _render_diff_section(entry: Dict[str, Any]) -> str:
    """Builds the HTML section containing the formatted diff for a key."""

    key = entry["key"]
    anchor = entry["anchor"]
    status = entry["status"]

    old_serialized, truncated_old = _prepare_serialized_for_diff(entry["old"])
    new_serialized, truncated_new = _prepare_serialized_for_diff(entry["new"])

    old_lines = old_serialized.splitlines(keepends=True)
    new_lines = new_serialized.splitlines(keepends=True)
    diff_lines = _diff_lines(old_lines, new_lines)
    cleaned_lines = list(diff_lines)
    if len(cleaned_lines) >= 2 and cleaned_lines[0].startswith("---") and cleaned_lines[1].startswith("+++"):
        cleaned_lines = cleaned_lines[2:]

    diff_html = _render_diff_lines(cleaned_lines, truncated_old or truncated_new)

    return "\n".join(
        [
            f'<section id="diff-{anchor}" class="gitdiff-block {status}">',
            f"<h3><code>{html.escape(key)}</code></h3>",
            f'<pre class="gitdiff">{diff_html}</pre>',
            "</section>",
        ]
    )


def _build_git_entries(diff: DiffResult, anchors: Dict[str, str]) -> List[Dict[str, Any]]:
    """Prepares the ordered list of entries to render as detailed diff sections."""

    entries: List[Dict[str, Any]] = []

    for key in diff.added:
        entries.append(
            {
                "key": key,
                "anchor": anchors[key],
                "status": "added",
                "old": _MISSING,
                "new": diff.added_values.get(key, _MISSING),
            }
        )

    for key in diff.removed:
        entries.append(
            {
                "key": key,
                "anchor": anchors[key],
                "status": "removed",
                "old": diff.removed_values.get(key, _MISSING),
                "new": _MISSING,
            }
        )

    for key in sorted(diff.changed):
        entries.append(
            {
                "key": key,
                "anchor": anchors[key],
                "status": "changed",
                "old": diff.changed[key]["old"],
                "new": diff.changed[key]["new"],
            }
        )

    return entries


def _render_git_sections(entries: List[Dict[str, Any]]) -> str:
    """Renders the diff sections for all tracked keys."""

    if not entries:
        return ""

    parts: List[str] = ['<section class="gitdiff-container">', '<h2>Diff</h2>']
    parts.extend(
        [
            '<pre class="gitdiff gitdiff-legend">',
            '<span class="ctx">--- old</span>',
            '<span class="ctx">+++ new</span>',
            '</pre>',
        ]
    )

    parts.extend(_render_diff_section(entry) for entry in entries)
    parts.append("</section>")
    return "\n".join(parts)


def _render_summary_card(title: str, css_class: str, items_html: str) -> str:
    """Renders an individual summary card with its entries."""

    parts = [f'<details class="summary-card {css_class}" open>', f"<summary>{title}</summary>"]
    if items_html:
        parts.extend(['<ul class="summary-list">', items_html, '</ul>'])
    else:
        parts.append('<p class="empty">No entries.</p>')
    parts.append('</details>')
    return "\n".join(parts)


def _render_summary_panel(diff: DiffResult, anchor_map: Dict[str, str]) -> str:
    """Builds the summary panel grouping added, removed and changed keys."""

    added_keys = list(diff.added)
    removed_keys = list(diff.removed)
    changed_keys = sorted(diff.changed)

    added_items = "".join(
        f'<li><a href="#diff-{html.escape(anchor_map[key])}"><code>{html.escape(key)}</code></a></li>'
        for key in added_keys
    )
    removed_items = "".join(
        f'<li><a href="#diff-{html.escape(anchor_map[key])}"><code>{html.escape(key)}</code></a></li>'
        for key in removed_keys
    )
    changed_items = "".join(
        "".join(
            [
                "<li>",
                f'<a href="#diff-{html.escape(anchor_map[key])}" class="change-link">',
                f'<span class="change-key"><code>{html.escape(key)}</code></span>',
                "</a>",
                "</li>",
            ]
        )
        for key in changed_keys
    )

    summary_cards = "\n".join(
        [
            _render_summary_card("Added", "added", added_items),
            _render_summary_card("Removed", "removed", removed_items),
            _render_summary_card("Changed", "changed", changed_items),
        ]
    )

    summary_counts = (
        "Added: {added}&nbsp;·&nbsp;Removed: {removed}&nbsp;·&nbsp;Changed: {changed}"
    ).format(
        added=len(diff.added),
        removed=len(diff.removed),
        changed=len(diff.changed),
    )

    panel_parts = [
        '<section class="summary-panel">',
        '<div class="summary-header"><h2>Summary</h2></div>',
        '<div class="summary-grid">',
        summary_cards,
        '</div>',
    ]

    if not diff.has_differences:
        panel_parts.append('<p class="empty-state">No differences.</p>')

    panel_parts.extend(['<footer class="summary-footer">', summary_counts, '</footer>', '</section>'])
    return "\n".join(panel_parts)


def render_html(diff: DiffResult) -> str:
    """Builds the HTML report for a diff result."""

    styles = """
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }
        section { padding: 1rem; border: 1px solid #cbd5f5; border-radius: 12px; margin-bottom: 1.5rem; background: #ffffff; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08); }
        section h2 { margin-top: 0; color: #0f172a; }
        section ul { margin: 0; padding-left: 1.5rem; }
        section.empty { color: #64748b; font-style: italic; background: #f1f5f9; border-style: dashed; }
        footer { font-weight: bold; margin-top: 2rem; color: #0f172a; }
        code {
            font-family: "Fira Code", "Courier New", monospace;
            white-space: pre-wrap;
            word-break: break-word;
            color: #0f172a;
        }
        a { color: #2563eb; text-decoration: none; }
        a:hover { color: #1d4ed8; text-decoration: none; }
        .summary-panel { padding: 1.75rem; border: 2px solid #cbd5f5; border-radius: 20px; margin-bottom: 2rem; background: linear-gradient(135deg, rgba(226, 232, 240, 0.5), rgba(255, 255, 255, 0.95)); box-shadow: 0 18px 40px rgba(15, 23, 42, 0.1); }
        .summary-header h2 { margin: 0; text-transform: uppercase; letter-spacing: 0.04em; color: #1e293b; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; margin-top: 1.25rem; }
        .summary-card { display: block; border: 2px solid #cbd5f5; border-radius: 16px; padding: 1rem 1.25rem; background: #ffffff; box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4); transition: transform 0.2s ease, box-shadow 0.2s ease; }
        .summary-card:hover { transform: translateY(-2px); box-shadow: 0 12px 22px rgba(15, 23, 42, 0.12); }
        .summary-card.added { border-color: #22c55e; background: linear-gradient(135deg, rgba(187, 247, 208, 0.65), rgba(255, 255, 255, 0.95)); }
        .summary-card.removed { border-color: #ef4444; background: linear-gradient(135deg, rgba(254, 202, 202, 0.65), rgba(255, 255, 255, 0.95)); }
        .summary-card.changed { border-color: #f97316; background: linear-gradient(135deg, rgba(254, 215, 170, 0.65), rgba(255, 255, 255, 0.95)); }
        .summary-card summary { list-style: none; display: flex; align-items: center; justify-content: space-between; font-weight: 600; font-size: 1.05rem; margin: 0; color: #0f172a; cursor: pointer; }
        .summary-card summary::after { content: "−"; font-size: 1.25rem; line-height: 1; color: #475569; }
        .summary-card:not([open]) summary::after { content: "+"; }
        .summary-card summary::marker { display: none; }
        .summary-card summary::-webkit-details-marker { display: none; }
        .summary-card[open] summary { margin-bottom: 0.75rem; }
        .summary-list { margin: 0; padding-left: 1.25rem; color: #1e293b; }
        .summary-card:not([open]) .summary-list, .summary-card:not([open]) .empty { display: none; }
        .summary-card .empty { margin: 0; color: #64748b; font-style: italic; }
        .summary-footer { margin-top: 1.75rem; text-align: right; font-weight: 600; color: #1e293b; }
        .empty-state { margin-top: 1.5rem; color: #64748b; font-style: italic; }
        .gitdiff-container { border: 1px solid #cbd5f5; border-radius: 16px; padding: 1.5rem; background: #ffffff; box-shadow: 0 12px 30px rgba(37, 99, 235, 0.12); }
        .gitdiff-container h2 { margin-top: 0; color: #1e293b; }
        .gitdiff-legend { margin: 0.5rem 0 1rem; border-radius: 10px; background: #f1f5f9; padding: 0.75rem 1rem; display: inline-block; }
        .gitdiff-legend span { display: block; font-weight: 600; color: #475569; }
        .gitdiff-block { border: 1px solid #cbd5f5; border-radius: 12px; padding: 1rem 1.25rem; background: linear-gradient(135deg, rgba(224, 231, 255, 0.65), rgba(255, 255, 255, 0.95)); margin-top: 1rem; }
        .gitdiff-block.added { border-color: #22c55e; background: linear-gradient(135deg, rgba(187, 247, 208, 0.7), rgba(236, 253, 245, 0.95)); }
        .gitdiff-block.removed { border-color: #ef4444; background: linear-gradient(135deg, rgba(254, 202, 202, 0.7), rgba(254, 242, 242, 0.95)); }
        .gitdiff-block.changed { border-color: #f97316; background: linear-gradient(135deg, rgba(254, 215, 170, 0.7), rgba(255, 247, 237, 0.95)); }
        .gitdiff-block h3 { margin-top: 0; color: #0f172a; }
        .gitdiff { font-family: "Fira Code", "Courier New", monospace; padding: 1rem; border-radius: 10px; background: #f1f5f9; color: #0f172a; overflow-x: auto; }
        .gitdiff span { display: block; padding: 0.15rem 0.35rem; border-radius: 6px; }
        .gitdiff .add { background: #dcfce7; color: #14532d; }
        .gitdiff .del { background: #fee2e2; color: #991b1b; }
        .gitdiff .ctx { color: #475569; }
        .gitdiff .hunk { background: #dbeafe; color: #1d4ed8; font-weight: 600; }
        .change-link { display: inline-flex; flex-wrap: wrap; gap: 0.35rem; align-items: baseline; color: inherit; }
        .change-key { font-weight: 600; }
        .change-link code { color: inherit; }
        .change-values { color: #475569; }
        .change-link:hover { color: #1d4ed8; }
        .change-link:hover code { color: inherit; }
        .gitdiff-container a { color: inherit; text-decoration: none; }
        .gitdiff-container a:hover { color: inherit; text-decoration: none; }
        .full-json-section { border: 1px solid #cbd5f5; border-radius: 16px; padding: 1.5rem; background: #ffffff; box-shadow: 0 12px 30px rgba(37, 99, 235, 0.12); }
        .full-json-details summary { font-weight: 600; cursor: pointer; color: #1e293b; }
        .full-json-details summary:focus { outline: none; }
        .full-json-wrapper { margin-top: 1rem; overflow-x: auto; }
        .full-json-table { width: 100%; border-collapse: collapse; }
        .full-json-table th { text-align: left; padding: 0.75rem; background: #e2e8f0; color: #0f172a; }
        .full-json-table td { padding: 0; vertical-align: top; }
        .full-json-table td pre { margin: 0; padding: 0.5rem 0.75rem; font-family: "Fira Code", "Courier New", monospace; white-space: pre; background: transparent; color: inherit; }
        .full-json-table .code-cell { border-top: 1px solid #e2e8f0; background: #f8fafc; }
        .full-json-table .code-cell.ctx { color: #0f172a; }
        .full-json-table .code-cell.del { background: #fee2e2; color: #991b1b; }
        .full-json-table .code-cell.mix { background: #ffedd5; color: #c2410c; }
        .full-json-table .code-cell.empty { color: #cbd5f5; }
    </style>
    """.strip()

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        "<title>JSON Pretty Diff</title>",
        styles,
        "</head>",
        "<body>",
        "<h1>JSON Pretty Diff</h1>",
    ]

    used_anchors: Dict[str, int] = {}
    anchor_map: Dict[str, str] = {}
    for key in list(diff.added) + list(diff.removed) + sorted(diff.changed):
        if key not in anchor_map:
            anchor_map[key] = _sanitize_anchor(key, used_anchors)

    summary_panel = _render_summary_panel(diff, anchor_map)
    html_parts.append(summary_panel)

    git_entries = _build_git_entries(diff, anchor_map)
    git_sections = _render_git_sections(git_entries)
    if git_sections:
        html_parts.append(git_sections)

    full_json_section = _render_full_json_section(diff)
    if full_json_section:
        html_parts.append(full_json_section)

    html_parts.append("</body>")
    html_parts.append("</html>")
    return "\n".join(html_parts)
