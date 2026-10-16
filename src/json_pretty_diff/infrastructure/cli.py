"""Command-line interface for JSON Pretty Diff."""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, Dict, List, NoReturn, Sequence

from ..application.use_cases import DiffUseCase
from ..domain.models import DiffResult
from ..presentation.html_renderer import render_html
from ..version import __version__
from ._io import (
    InputOutputError,
    load_json_object,
    shown_path,
    write_line,
    write_report,
    write_report_to_stream,
)
from ._output import to_stderr, to_stdout


class JsonPrettyDiffCLI:
    """Facade that exposes the command-line entry point.

    ``run`` returns the exit code (0: no differences, 1: differences) and raises
    ``SystemExit`` for ``--help``, ``--version`` and errors (code 2), as the script does.

    >>> try:
    ...     JsonPrettyDiffCLI().run(["--version"])
    ... except SystemExit as stop:
    ...     print("exit", stop.code)
    jpd 1...
    exit 0
    """

    def __init__(self) -> None:
        """Initializes the CLI parser."""

        description = dedent(
            """
            Generate an HTML diff between two JSON files.

            Quick start after running `pip install json-pretty-diff`:
              1. Pick the original JSON document as the source file.
              2. Pick the updated JSON document as the target file.
              3. Execute `jpd source.json target.json -o diff.html`.
              4. Open `diff.html` in your browser to review the styled report.
            """
        ).strip()

        self._parser = argparse.ArgumentParser(
            prog="jpd",
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {__version__}",
        )
        self._parser.add_argument("source", help="Path to the original JSON file.")
        self._parser.add_argument("target", help="Path to the modified JSON file.")
        self._parser.add_argument(
            "-o",
            "--output",
            help="Path to the output HTML file. When omitted, the HTML is sent to stdout.",
        )
        self._parser.add_argument(
            "--open",
            action="store_true",
            help="Open the generated HTML report in the default browser (requires -o).",
        )
        self._parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Suppress all output except errors.",
        )
        self._parser.add_argument(
            "--no-style",
            action="store_true",
            help="Generate HTML without CSS styles (lighter output).",
        )
        self._parser.add_argument(
            "--no-timestamp",
            action="store_true",
            help="Leave the generation time out, so the same inputs give the same report.",
        )
        self._parser.epilog = "When `--output` is omitted, redirect the standard output to a file with `>` if you want to keep the report."
        self._use_case = DiffUseCase()

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Executes the CLI with the provided arguments.

        Returns
        -------
        int
            Exit status code: ``0`` when no differences are detected, ``1`` when
            changes exist. Errors print ``Error: ...`` and raise ``SystemExit(2)``.
        """

        args = self._parser.parse_args(argv)

        if args.open and not args.output:
            self._fail("--open requires -o/--output to be specified.")

        warnings: List[str] = []
        source = self._load_json(Path(args.source), warnings)
        target = self._load_json(Path(args.target), warnings)
        # The same file given twice warns once.
        warnings = list(dict.fromkeys(warnings))

        try:
            diff = self._use_case.execute(source, target)
            html_report = render_html(
                diff,
                include_styles=not args.no_style,
                include_timestamp=not args.no_timestamp,
                warnings=warnings,
            )
        except RecursionError as error:
            names = f"{shown_path(args.source)} or {shown_path(args.target)}"
            self._fail(f"{names} is nested too deeply to compare.", error)

        if not args.quiet:
            for message in warnings:
                to_stderr("Warning", message)

        if args.output:
            output_path = Path(args.output)
            self._guard(lambda: write_report(output_path, html_report))
            # Without a standard output (pythonw, a closed descriptor) the status line is skipped.
            if not args.quiet and sys.stdout is not None:
                line = f"Report saved to {output_path} ({self._summarize(diff)})\n"
                self._guard(lambda: to_stdout(lambda: write_line(line)))
            if args.open:
                webbrowser.open(output_path.resolve().as_uri())
        elif not args.quiet:
            ending = "" if html_report.endswith("\n") else "\n"
            self._guard(lambda: to_stdout(lambda: write_report_to_stream(html_report + ending)))

        return 1 if diff.has_differences else 0

    def _load_json(self, path: Path, warnings: List[str]) -> Dict[str, Any]:
        """Loads a JSON file from disk ensuring it is an object."""

        try:
            return load_json_object(path, warnings)
        except InputOutputError as error:
            self._fail(str(error), error)

    def _guard(self, action: Callable[[], object]) -> None:
        """Runs an output step; a failure becomes ``Error: ...`` and exit code 2."""

        try:
            action()
        except InputOutputError as error:
            self._fail(str(error), error)

    @staticmethod
    def _summarize(diff: DiffResult) -> str:
        """Builds a short summary like ``"2 added, 1 removed, 0 changed"``."""

        if not diff.has_differences:
            return "no differences"
        return f"{len(diff.added)} added, {len(diff.removed)} removed, {len(diff.changed)} changed"

    @staticmethod
    def _fail(message: str, cause: BaseException | None = None) -> NoReturn:
        """Writes ``Error: message`` to stderr and exits with code 2."""

        to_stderr("Error", message)
        raise SystemExit(2) from cause
