"""Command-line interface for JSON Pretty Diff."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Sequence

from application.use_cases import DiffUseCase
from presentation.html_renderer import render_html
from version import __version__


class JsonPrettyDiffCLI:
    """Facade that exposes the command-line entry point."""

    def __init__(self) -> None:
        """Initializes the CLI parser."""

        self._parser = argparse.ArgumentParser(
            prog="jpd",
            description="Generate an HTML diff between two JSON files.",
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
        self._use_case = DiffUseCase()

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Executes the CLI with the provided arguments."""

        args = self._parser.parse_args(argv)
        source = self._load_json(Path(args.source))
        target = self._load_json(Path(args.target))

        diff = self._use_case.execute(source, target)
        html_report = render_html(diff)

        if args.output:
            self._write_output(Path(args.output), html_report)
        else:
            sys.stdout.write(html_report)
            if not html_report.endswith("\n"):
                sys.stdout.write("\n")

        return 1 if diff.has_differences else 0

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Loads a JSON file from disk ensuring it is an object."""

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            self._emit_error(f"Archivo no encontrado: {path}")
            raise SystemExit(2) from error
        except json.JSONDecodeError as error:
            self._emit_error(f"JSON inválido en {path}: {error.msg}")
            raise SystemExit(2) from error

        if not isinstance(data, dict):
            self._emit_error(f"La raíz del archivo {path} debe ser un objeto JSON.")
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
