"""Full JSON section rendering helpers for the HTML renderer."""

from __future__ import annotations

import html
import json
from difflib import SequenceMatcher
from typing import Any, List

from ...domain.models import DiffResult

FULL_JSON_TABLE_ID = "full-json-table"

def _serialize_full_json(data: Any) -> str:
    """Serializes the complete JSON snapshot preserving readability."""

    try:
        return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(data)

def _build_side_by_side_rows(old_lines: List[str], new_lines: List[str]) -> str:
    """Creates table rows that highlight line-level differences."""

    matcher = SequenceMatcher(None, old_lines, new_lines)
    rows: List[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_chunk = old_lines[i1:i2]
        new_chunk = new_lines[j1:j2]
        limit = max(len(old_chunk), len(new_chunk)) or 1

        for index in range(limit):
            old_line = old_chunk[index] if index < len(old_chunk) else ""
            new_line = new_chunk[index] if index < len(new_chunk) else ""

            left_class = "left"
            if tag == "replace":
                right_class = "diff-modified"
            elif tag == "delete":
                right_class = "diff-removed"
            elif tag == "insert":
                right_class = "diff-added"
            else:
                right_class = "neutral"

            old_cell = html.escape(old_line) if old_line else "&nbsp;"
            new_cell = html.escape(new_line) if new_line else "&nbsp;"

            rows.append(
                "".join(
                    [
                        "<tr>",
                        f'<td class="code-cell {left_class}"><pre>{old_cell}</pre></td>',
                        f'<td class="code-cell {right_class}"><pre>{new_cell}</pre></td>',
                        "</tr>",
                    ]
                )
            )

    return "\n".join(rows)

def render_full_json_section(diff: DiffResult) -> str:
    """Renders the expandable section that shows both JSON snapshots."""

    if not diff.source_snapshot and not diff.target_snapshot:
        return ""

    old_serialized = _serialize_full_json(diff.source_snapshot)
    new_serialized = _serialize_full_json(diff.target_snapshot)

    old_lines = old_serialized.splitlines()
    new_lines = new_serialized.splitlines()
    table_rows = _build_side_by_side_rows(old_lines, new_lines)

    table_id = FULL_JSON_TABLE_ID

    return "\n".join(
        [
            '<section class="full-json-section page-section">',
            '<details class="panel-toggle full-json-details" open>',
            '<summary>FULL JSON</summary>',
            '<div class="full-json-wrapper">',
            '<div class="full-json-filter">',
            '<div class="full-json-filter__field">',
            '<label for="full-json-filter" class="full-json-filter__label">Search</label>',
            (
                '<input id="full-json-filter" '
                'class="full-json-filter__input" '
                'type="search" '
                'placeholder="Type to highlight..." '
                'data-json-filter="true" '
                f'data-json-target="{table_id}" />'
            ),
            '</div>',
            f'<table id="{table_id}" class="full-json-table">',
            "<thead>",
            "<tr>",
            "<th>Old JSON</th>",
            "<th>New JSON</th>",
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


__all__ = [
    "FULL_JSON_TABLE_ID",
    "render_full_json_section",
]
