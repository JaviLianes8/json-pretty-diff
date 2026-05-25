"""Console script integration for JSON Pretty Diff."""

from __future__ import annotations

from .infrastructure.cli import JsonPrettyDiffCLI

def main() -> int:
    """Entry point used by the console script."""

    return JsonPrettyDiffCLI().run()

__all__ = ["main", "JsonPrettyDiffCLI"]
