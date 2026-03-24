"""Command-line interface for JSON Pretty Diff."""

import argparse
import json
import sys
import webbrowser
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Sequence

from ..application.use_cases import DiffUseCase
from ..presentation.html_renderer import render_html
from ..version import __version__

class JsonPrettyDiffCLI:
    """Facade that exposes the command-line entry point."""

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
        self._parser.epilog = (
            "When `--output` is omitted, redirect the standard output to a file with `>` if you want to keep the report."
        )
        self._use_case = DiffUseCase()

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Executes the CLI with the provided arguments.

        Returns
        -------
        int
            Exit status code: ``0`` when no differences are detected, ``1`` when
            changes exist, and ``2`` when a recoverable error is reported.
        """

        args = self._parser.parse_args(argv)

        if args.open and not args.output:
            self._emit_error("--open requires -o/--output to be specified.")
            raise SystemExit(2)

        source = self._load_json(Path(args.source))
        target = self._load_json(Path(args.target))

        diff = self._use_case.execute(source, target)
        html_report = render_html(diff, include_styles=not args.no_style)

        if args.output:
            output_path = Path(args.output)
            self._write_output(output_path, html_report)
            if not args.quiet:
                status = "differences found" if diff.has_differences else "no differences"
                sys.stdout.write(f"Report saved to {output_path} ({status})\n")
            if args.open:
                webbrowser.open(output_path.resolve().as_uri())
        else:
            if not args.quiet:
                sys.stdout.write(html_report)
                if not html_report.endswith("\n"):
                    sys.stdout.write("\n")

        return 1 if diff.has_differences else 0

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Loads a JSON file from disk ensuring it is an object."""

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            self._emit_error(f"File not found: {path}")
            raise SystemExit(2) from error
        except json.JSONDecodeError as error:
            self._emit_error(f"Invalid JSON in {path}: {error.msg}")
            raise SystemExit(2) from error

        if not isinstance(data, dict):
            self._emit_error(f"The root element of {path} must be a JSON object.")
            raise SystemExit(2)

        return data

    def _write_output(self, path: Path, html_report: str) -> None:
        """Persists the HTML report to the specified path."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html_report, encoding="utf-8")

    @staticmethod
    def _emit_error(message: str) -> None:
        """Writes an error message to stderr."""

        sys.stderr.write(f"Error: {message}\n")
