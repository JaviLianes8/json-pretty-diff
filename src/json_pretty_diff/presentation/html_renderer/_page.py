"""High-level HTML page renderer for JSON Pretty Diff."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Dict, Sequence

from ...domain.models import DiffResult
from ...version import __version__
from ._anchors import sanitize_anchor
from ._branding import render_branding_header
from ._diff_data import build_git_entries
from ._diff_view import render_git_sections
from ._full_json import FULL_JSON_TABLE_ID, render_full_json_section
from ._full_json_script import render_full_json_filter_script
from ._styles import STYLES
from ._summary import render_summary_panel

# Control characters other than tab, line feed and carriage return are not allowed in HTML
# text; those coming from key names or warnings are shown as \uXXXX escapes instead.
_CONTROLS = {code: f"\\u{code:04x}" for code in [*range(0x20), 0x7F] if code not in (9, 10, 13)}
_WARNINGS_STYLE =' style="border-color: #f59e0b; background: #fffbeb;"'


def render_html(
    diff: DiffResult,
    *,
    include_styles: bool = True,
    include_timestamp: bool = True,
    warnings: Sequence[str] = (),
) -> str:
    """Builds the complete HTML report for a diff result.

    ``include_styles=False`` leaves the stylesheet out. ``include_timestamp=False`` leaves the
    generation time out, so the same diff always gives the same page. Each entry of
    ``warnings`` becomes an item of a "Warnings" section above the summary; the section is
    absent when there are none.

    >>> from json_pretty_diff import compute_top_level_diff, render_html
    >>> page = render_html(compute_top_level_diff({"a": 1}, {"a": 2}), include_timestamp=False)
    >>> page.startswith("<!DOCTYPE html>") and page.endswith("</html>")
    True
    >>> "json-pretty-diff v" in page and "Generated on" not in page
    True
    """

    if isinstance(warnings, str) or not all(isinstance(item, str) for item in warnings):
        raise TypeError("warnings must be a sequence of strings")

    if include_timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        generated = f"Generated on {timestamp} - v{__version__}"
    else:
        generated = f"json-pretty-diff v{__version__}"

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        "<title>JSON Pretty Diff</title>",
        STYLES if include_styles else "",
        "</head>",
        "<body>",
        render_branding_header(),
        "<h1>JSON Pretty Diff</h1>",
        f'<p style="color: #64748b; font-size: 0.9rem;">{generated}</p>',
    ]

    if warnings:
        html_parts.append(_render_warnings(warnings, include_styles))

    used_anchors: Dict[str, int] = {}
    anchor_map: Dict[str, str] = {}
    for key in list(diff.added) + list(diff.removed) + sorted(diff.changed):
        if key not in anchor_map:
            anchor_map[key] = sanitize_anchor(key, used_anchors)

    summary_panel = render_summary_panel(diff, anchor_map)
    html_parts.append(summary_panel)

    git_entries = build_git_entries(diff, anchor_map)
    git_sections = render_git_sections(git_entries)
    if git_sections:
        html_parts.append(git_sections)

    full_json_section = render_full_json_section(diff)
    if full_json_section:
        html_parts.append(full_json_section)
        html_parts.append(render_full_json_filter_script(FULL_JSON_TABLE_ID))

    html_parts.append("</body>")
    html_parts.append("</html>")
    return "\n".join(html_parts).translate(_CONTROLS)


def _render_warnings(warnings: Sequence[str], include_styles: bool) -> str:
    """Lists what the inputs hold that RFC 8259 does not allow or advises against."""

    style = _WARNINGS_STYLE if include_styles else ""
    items = "".join(f"<li>{html.escape(message)}</li>" for message in warnings)
    return "\n".join(
        [
            f'<section class="warnings page-section"{style}>',
            "<h2>Warnings</h2>",
            f'<ul class="warnings-list">{items}</ul>',
            "</section>",
        ]
    )


__all__ = ["render_html"]
