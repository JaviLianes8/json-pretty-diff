"""Console script integration for JSON Pretty Diff."""

from __future__ import annotations

from .infrastructure.cli import JsonPrettyDiffCLI


def main() -> int:
    """Entry point used by the console script: runs ``jpd`` on ``sys.argv``.

    Returns the exit code (0: no differences, 1: differences); errors exit with 2.

    >>> from json_pretty_diff import main
    >>> callable(main)
    True
    """

    return JsonPrettyDiffCLI().run()


__all__ = ["JsonPrettyDiffCLI", "main"]
