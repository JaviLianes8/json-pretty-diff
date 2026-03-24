"""High-level HTML page renderer for JSON Pretty Diff."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from ...domain.models import DiffResult
from ...version import __version__
from ._anchors import sanitize_anchor
from ._branding import render_branding_header
from ._diff_data import build_git_entries
from ._diff_view import render_git_sections
from ._full_json import FULL_JSON_TABLE_ID, render_full_json_section
from ._full_json_script import render_full_json_filter_script
from ._summary import render_summary_panel

def render_html(diff: DiffResult, *, include_styles: bool = True) -> str:
    """Builds the complete HTML report for a diff result."""

    styles = """
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }
        .branding { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; margin: 1.5rem 0 2rem; }
        .branding__links { display: flex; gap: 0.9rem; }
        .branding__link img { border-radius: 50%; box-shadow: 0 6px 12px rgba(15, 23, 42, 0.18); transition: transform 0.2s ease, box-shadow 0.2s ease; }
        .branding__link:hover img { transform: translateY(-2px) scale(1.05); box-shadow: 0 12px 24px rgba(37, 99, 235, 0.25); }
        .branding__signature { margin: 0; font-weight: 500; color: #1e293b; }
        .branding__heart { color: #ef4444; margin-left: 0.35rem; }
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
        .panel-toggle { display: block; }
        .panel-toggle summary { list-style: none; display: flex; align-items: center; justify-content: space-between; font-weight: 700; font-size: 1.15rem; margin: 0; color: #0f172a; cursor: pointer; letter-spacing: 0.05em; }
        .panel-toggle summary::after { content: "−"; font-size: 1.35rem; line-height: 1; color: #475569; }
        .panel-toggle:not([open]) summary::after { content: "+"; }
        .panel-toggle summary::marker { display: none; }
        .panel-toggle summary::-webkit-details-marker { display: none; }
        .page-section { margin-bottom: 0; }
        .page-section + .page-section { margin-top: 2rem; }
        .summary-body { margin-top: 1.5rem; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.25rem; margin-top: 1.25rem; }
        .summary-card { display: block; border: 2px solid #cbd5f5; border-radius: 16px; padding: 1rem 1.25rem; background: #ffffff; box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4); transition: transform 0.2s ease, box-shadow 0.2s ease; }
        .summary-card:hover { transform: translateY(-2px); box-shadow: 0 12px 22px rgba(15, 23, 42, 0.12); }
        .summary-card.added { border-color: #22c55e; background: linear-gradient(135deg, rgba(187, 247, 208, 0.65), rgba(255, 255, 255, 0.95)); }
        .summary-card.removed { border-color: #ef4444; background: linear-gradient(135deg, rgba(254, 202, 202, 0.65), rgba(255, 255, 255, 0.95)); }
        .summary-card.changed { border-color: #f97316; background: linear-gradient(135deg, rgba(254, 215, 170, 0.65), rgba(255, 255, 255, 0.95)); }
        .summary-title { margin: 0 0 0.75rem; font-weight: 600; font-size: 1.05rem; color: #0f172a; }
        .summary-list { margin: 0; padding-left: 1.25rem; color: #1e293b; }
        .summary-card .empty { margin: 0; color: #64748b; font-style: italic; }
        .summary-footer { margin-top: 1.75rem; text-align: right; font-weight: 600; color: #1e293b; }
        .empty-state { margin-top: 1.5rem; color: #64748b; font-style: italic; }
        .gitdiff-container { border: 1px solid #cbd5f5; border-radius: 16px; padding: 1.5rem; background: #ffffff; box-shadow: 0 12px 30px rgba(37, 99, 235, 0.12); }
        .gitdiff-body { margin-top: 1.25rem; }
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
        .truncated-details { margin-top: 1rem; display: block; }
        .truncated-details summary { list-style: none; font-weight: 600; cursor: pointer; color: #1e293b; }
        .truncated-details summary::marker { display: none; }
        .truncated-details summary::-webkit-details-marker { display: none; }
        .truncated-wrapper { margin-top: 0.75rem; display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
        .truncated-column { border: 1px solid #cbd5f5; border-radius: 12px; background: #f8fafc; padding: 0.75rem; box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.5); }
        .truncated-title { margin: 0 0 0.5rem; font-size: 0.95rem; color: #0f172a; }
        .truncated-column.truncated-new { color: #0f172a; }
        .truncated-column.truncated-new--added { background: #dcfce7; border-color: #22c55e; color: #14532d; }
        .truncated-column.truncated-new--changed { background: #ffedd5; border-color: #f97316; color: #9a3412; }
        .truncated-column.truncated-new--removed { background: #fee2e2; border-color: #ef4444; color: #991b1b; }
        .truncated-column pre { margin: 0; font-family: "Fira Code", "Courier New", monospace; white-space: pre-wrap; word-break: break-word; color: inherit; }
        .full-json-section { border: 1px solid #cbd5f5; border-radius: 16px; padding: 1.5rem; background: #ffffff; box-shadow: 0 12px 30px rgba(37, 99, 235, 0.12); }
        .full-json-details summary { color: #1e293b; }
        .full-json-details summary:focus { outline: none; }
        .full-json-details[open] .full-json-wrapper { margin-top: 1rem; }
        .full-json-wrapper { overflow-x: auto; }
        .full-json-filter {
            position: sticky;
            top: 1rem;
            z-index: 5;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.75rem 1rem;
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            justify-content: space-between;
            width: 100%;
            box-sizing: border-box;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(248, 250, 252, 0.94));
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 0.85rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.14);
            backdrop-filter: blur(4px);
        }
        .full-json-filter__field { display: flex; align-items: center; gap: 0.75rem; flex: 1 1 320px; min-width: 260px; }
        .full-json-filter__label { font-weight: 600; color: #1e293b; white-space: nowrap; }
        .full-json-filter__input { flex: 1 1 auto; min-width: 0; padding: 0.5rem 0.75rem; border: 1px solid #cbd5f5; border-radius: 0.75rem; background: #f8fafc; color: #0f172a; }
        .full-json-filter__input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2); }
        .full-json-highlight { background: #fde68a; color: #7c2d12; border-radius: 0.35rem; padding: 0 0.2rem; box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.6); }
        .full-json-table { width: 100%; border-collapse: collapse; }
        .full-json-table th { text-align: left; padding: 0.75rem; background: #e2e8f0; color: #0f172a; }
        .full-json-table td { padding: 0; vertical-align: top; }
        .full-json-table td pre { margin: 0; padding: 0.5rem 0.75rem; font-family: "Fira Code", "Courier New", monospace; white-space: pre; background: transparent; color: inherit; }
        .full-json-table .code-cell { border-top: 1px solid #e2e8f0; background: #ffffff; color: #0f172a; }
        .full-json-table .code-cell.left { background: #ffffff; }
        .full-json-table .code-cell.neutral { background: #ffffff; }
        .full-json-table .code-cell.diff-added { background: #dcfce7; color: #14532d; }
        .full-json-table .code-cell.diff-modified { background: #ffedd5; color: #9a3412; }
        .full-json-table .code-cell.diff-removed { background: #fee2e2; color: #991b1b; }
    </style>
    """.strip()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1" />',
        "<title>JSON Pretty Diff</title>",
        styles if include_styles else "",
        "</head>",
        "<body>",
        render_branding_header(),
        "<h1>JSON Pretty Diff</h1>",
        f'<p style="color: #64748b; font-size: 0.9rem;">Generated on {timestamp} &mdash; v{__version__}</p>',
    ]

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
    return "\n".join(html_parts)

__all__ = ["render_html"]
