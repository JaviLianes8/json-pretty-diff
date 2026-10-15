"""Public package interface for JSON Pretty Diff.

Compare two JSON objects key by key and render the result as a self-contained HTML page.

>>> from json_pretty_diff import compute_top_level_diff
>>> diff = compute_top_level_diff({"name": "a", "old": 1}, {"name": "b", "new": 2})
>>> diff.added, diff.removed, list(diff.changed)
(['new'], ['old'], ['name'])
"""

from .application.use_cases import DiffUseCase
from .cli import main
from .domain.models import DiffResult
from .domain.services import compute_top_level_diff
from .infrastructure.cli import JsonPrettyDiffCLI
from .presentation.html_renderer import render_html
from .version import __version__

__all__ = [
    "DiffResult",
    "DiffUseCase",
    "JsonPrettyDiffCLI",
    "__version__",
    "compute_top_level_diff",
    "main",
    "render_html",
]
