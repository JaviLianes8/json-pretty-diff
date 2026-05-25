"""Summary panel rendering helpers for the HTML renderer."""

from __future__ import annotations

import html
from typing import Dict, Iterable, List

from ...domain.models import DiffResult

def _render_summary_card(title: str, css_class: str, items_html: str) -> str:
    """Builds a summary card with its item list."""

    parts = [f'<div class="summary-card {css_class}">', f'<h4 class="summary-title">{title}</h4>']
    if items_html:
        parts.extend(['<ul class="summary-list">', items_html, '</ul>'])
    else:
        parts.append('<p class="empty">No entries.</p>')
    parts.append('</div>')
    return "\n".join(parts)

def _render_key_links(keys: Iterable[str], anchor_map: Dict[str, str]) -> str:
    """Creates a list of links pointing to diff sections for the given keys."""

    return "".join(
        f'<li><a href="#diff-{html.escape(anchor_map[key])}"><code>{html.escape(key)}</code></a></li>'
        for key in keys
    )

def _render_changed_links(keys: Iterable[str], anchor_map: Dict[str, str]) -> str:
    """Creates the list of anchors used in the changed summary column."""

    items: List[str] = []
    for key in keys:
        anchor = html.escape(anchor_map[key])
        safe_key = html.escape(key)
        items.append(
            "".join(
                [
                    "<li>",
                    f'<a href="#diff-{anchor}" class="change-link">',
                    f'<span class="change-key"><code>{safe_key}</code></span>',
                    "</a>",
                    "</li>",
                ]
            )
        )
    return "".join(items)

def render_summary_panel(diff: DiffResult, anchor_map: Dict[str, str]) -> str:
    """Builds the summary panel grouping added, removed, and changed keys."""

    added_keys = list(diff.added)
    removed_keys = list(diff.removed)
    changed_keys = sorted(diff.changed)

    added_items = _render_key_links(added_keys, anchor_map)
    removed_items = _render_key_links(removed_keys, anchor_map)
    changed_items = _render_changed_links(changed_keys, anchor_map)

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
        '<section class="summary-panel page-section">',
        '<details class="panel-toggle summary-toggle" open>',
        '<summary>SUMMARY</summary>',
        '<div class="summary-body">',
        '<div class="summary-grid">',
        summary_cards,
        '</div>',
    ]

    if not diff.has_differences:
        panel_parts.append('<p class="empty-state">No differences.</p>')

    panel_parts.extend(
        ['<footer class="summary-footer">', summary_counts, '</footer>', '</div>', '</details>', '</section>']
    )
    return "\n".join(panel_parts)

__all__ = ["render_summary_panel"]
