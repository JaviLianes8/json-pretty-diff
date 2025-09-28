"""HTML rendering utilities for JSON Pretty Diff."""

import html
import json
from typing import Any

from jpd.domain.models import DiffResult


def _format_value(value: Any) -> str:
    """Returns an HTML-safe representation for a JSON value."""

    return html.escape(json.dumps(value, ensure_ascii=False))


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

    changed_items = "".join(
        (
            "<li><code>{key}</code>: <code>{old}</code> → <code>{new}</code></li>".format(
                key=html.escape(key),
                old=_format_value(values["old"]),
                new=_format_value(values["new"]),
            )
        )
        for key, values in sorted(diff.changed.items())
    )

    render_section("Added", "added", added_items)
    render_section("Removed", "removed", removed_items)
    render_section("Changed", "changed", changed_items)

    summary = f"Added: {len(diff.added)} · Removed: {len(diff.removed)} · Changed: {len(diff.changed)}"
    if not diff.has_differences:
        html_parts.append("<p>No differences.</p>")
    html_parts.append(f"<footer>{summary}</footer>")
    html_parts.append("</body>")
    html_parts.append("</html>")
    return "\n".join(html_parts)
