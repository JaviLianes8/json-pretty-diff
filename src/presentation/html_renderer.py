"""HTML rendering utilities for JSON Pretty Diff."""

import html
import json
from difflib import unified_diff
from typing import Any, Dict, Iterable, List, Tuple

from domain.models import DiffResult


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
        if line.startswith("+++") or line.startswith("---"):
            css_class = "ctx"
        elif line.startswith("@@"):
            css_class = "hunk"
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


def _render_diff_section(key: str, values: Dict[str, Any], anchor: str) -> str:
    """Builds the HTML section containing the git-style diff for a key."""

    old_serialized = _serialize_for_diff(values["old"])
    new_serialized = _serialize_for_diff(values["new"])

    truncated_old = False
    truncated_new = False
    old_serialized, truncated_old = _truncate_text(old_serialized)
    new_serialized, truncated_new = _truncate_text(new_serialized)

    old_lines = old_serialized.splitlines(keepends=True)
    new_lines = new_serialized.splitlines(keepends=True)
    diff_lines = _diff_lines(old_lines, new_lines)

    diff_html = _render_diff_lines(diff_lines, truncated_old or truncated_new)

    return "\n".join(
        [
            f'<section id="diff-{anchor}" class="gitdiff-block">',
            f"<h3><code>{html.escape(key)}</code></h3>",
            f'<pre class="gitdiff">{diff_html}</pre>',
            "</section>",
        ]
    )


def _render_git_sections(diff: DiffResult, keys: List[str], anchors: Dict[str, str]) -> str:
    """Renders the git-style diff sections for changed keys."""

    if not diff.changed:
        return ""

    parts: List[str] = ["<section class=\"gitdiff-container\">", "<h2>Git-style diff</h2>"]

    if len(keys) > 1:
        parts.append('<nav class="diff-index"><strong>Índice:</strong><ul>')
        parts.extend(
            f'<li><a href="#diff-{anchors[key]}"><code>{html.escape(key)}</code></a></li>'
            for key in keys
        )
        parts.append("</ul></nav>")

    parts.extend(_render_diff_section(key, diff.changed[key], anchors[key]) for key in keys)
    parts.append("</section>")
    return "\n".join(parts)


def render_html(diff: DiffResult) -> str:
    """Builds the HTML report for a diff result."""

    styles = """
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        section { padding: 1rem; border: 1px solid; border-radius: 8px; margin-bottom: 1.5rem; }
        section h2 { margin-top: 0; }
        section ul { margin: 0; padding-left: 1.5rem; }
        section.empty { color: #555; font-style: italic; }
        section.added { border-color: #2e7d32; background: #e8f5e9; }
        section.removed { border-color: #c62828; background: #ffebee; }
        section.changed { border-color: #f9a825; background: #fffde7; }
        footer { font-weight: bold; }
        code {
            font-family: "Fira Code", "Courier New", monospace;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .gitdiff-container { border: 1px solid #1e293b; border-radius: 8px; padding: 1rem; background: #0b1120; color: #e2e8f0; }
        .gitdiff-container h2 { margin-top: 0; }
        .gitdiff-container nav ul { list-style: none; padding-left: 0; display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .gitdiff-container nav li { margin: 0; }
        .gitdiff-container nav a { color: #93c5fd; text-decoration: none; }
        .gitdiff-container nav a:hover { text-decoration: underline; }
        .gitdiff-block { border: 1px solid #1e293b; border-radius: 8px; padding: 1rem; background: #111c34; }
        .gitdiff { font-family: monospace; padding: 1rem; border-radius: 8px; background: #0f172a; color: #e2e8f0; }
        .gitdiff .add { display: block; background: #064e3b; }
        .gitdiff .del { display: block; background: #7f1d1d; }
        .gitdiff .ctx { display: block; opacity: 0.8; }
        .gitdiff .hunk { display: block; color: #93c5fd; }
    </style>
    """.strip()

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\" />",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
        "<title>JSON Pretty Diff</title>",
        styles,
        "</head>",
        "<body>",
        "<h1>JSON Pretty Diff</h1>",
    ]

    def render_section(title: str, css_class: str, items: str) -> None:
        classes = f"{css_class} empty" if not items else css_class
        html_parts.append(f'<section class="{classes}">')
        html_parts.append(f"<h2>{title}</h2>")
        if items:
            html_parts.append("<ul>")
            html_parts.append(items)
            html_parts.append("</ul>")
        else:
            html_parts.append("<p>No entries.</p>")
        html_parts.append("</section>")

    added_items = "".join(f"<li><code>{html.escape(key)}</code></li>" for key in diff.added)
    removed_items = "".join(f"<li><code>{html.escape(key)}</code></li>" for key in diff.removed)

    changed_keys = sorted(diff.changed)
    used_anchors: Dict[str, int] = {}
    anchor_map = {key: _sanitize_anchor(key, used_anchors) for key in changed_keys}

    changed_items = "".join(
        (
            "<li><a href=\"#diff-{anchor}\"><code>{key}</code></a>: <code>{old}</code> → "
            "<code>{new}</code></li>".format(
                anchor=anchor_map[key],
                key=html.escape(key),
                old=_format_value(diff.changed[key]["old"]),
                new=_format_value(diff.changed[key]["new"]),
            )
        )
        for key in changed_keys
    )

    render_section("Added", "added", added_items)
    render_section("Removed", "removed", removed_items)
    render_section("Changed", "changed", changed_items)

    summary = f"Added: {len(diff.added)} · Removed: {len(diff.removed)} · Changed: {len(diff.changed)}"
    if not diff.has_differences:
        html_parts.append("<p>No differences.</p>")
    html_parts.append(f"<footer>{summary}</footer>")
    git_sections = _render_git_sections(diff, changed_keys, anchor_map) if diff.changed else ""
    if git_sections:
        html_parts.append(git_sections)
    html_parts.append("</body>")
    html_parts.append("</html>")
    return "\n".join(html_parts)
