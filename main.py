"""Application entry point for JSON Pretty Diff."""

from __future__ import annotations

from pathlib import Path
import sys


def _ensure_src_on_path() -> None:
    """Adds the local ``src`` directory to ``sys.path`` when running from source."""

    project_root = Path(__file__).resolve().parent
    src_directory = project_root / "src"
    if src_directory.exists():
        src_path = str(src_directory)
        if src_path not in sys.path:
            sys.path.insert(0, src_path)


_ensure_src_on_path()

from json_pretty_diff.infrastructure.cli import JsonPrettyDiffCLI  # noqa: E402  (import after path setup)


def main() -> int:
    """Runs the JSON Pretty Diff command-line interface."""

    return JsonPrettyDiffCLI().run()


if __name__ == "__main__":
    raise SystemExit(main())
