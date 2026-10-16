"""The documented differences between a 1.1.1 report and a 1.2.0 report, as an edit.

Applying these edits to a report rendered by 1.1.1 must give exactly what 1.2.0 renders for
the same input, which proves that nothing else in the page changed.
"""

from __future__ import annotations

import re

from json_pretty_diff.presentation.html_renderer._branding import SOCIAL_LINKS
from json_pretty_diff.presentation.html_renderer._full_json_script import (
    render_full_json_filter_script,
)

ICONS_1_1_1 = (
    "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg",
    "https://cdn.simpleicons.org/github/181717",
    "https://cdn.simpleicons.org/buymeacoffee/FFDD00",
)
_PRE = re.compile(r'(<pre class="gitdiff(?: gitdiff-legend)?">)(.*?)(</pre>)', re.S)
_SPAN = re.compile(r'<span class="(\w+)">(.*?)</span>', re.S)


def _rows(match: re.Match[str]) -> str:
    spans = _SPAN.findall(match.group(2))
    body = "".join(
        f'<span class="{css}">{text[:-1] if text.endswith(chr(10)) else text}\n</span>'
        for css, text in spans
    )
    return match.group(1) + body + match.group(3)


def upgrade_1_1_1(report: str, version: str) -> str:
    """Edit a 1.1.1 report into the 1.2.0 report for the same input."""
    report = report.replace("&mdash; v1.1.1</p>", f"- v{version}</p>")
    for old, (_, _, new) in zip(ICONS_1_1_1, SOCIAL_LINKS):
        report = report.replace(f'src="{old}"', f'src="{new}"')
    report = _search(report)
    return _PRE.sub(_rows, report)


def _search(report: str) -> str:
    """Swap in the new highlightText, which matches on the text itself (no lowercasing)."""
    start, end = "    function highlightText(", "    function ensureMatchVisible("
    if start not in report:
        return report
    new = render_full_json_filter_script("full-json-table")
    new_body = new[new.index(start) : new.index(end)]
    return report[: report.index(start)] + new_body + report[report.index(end) :]
