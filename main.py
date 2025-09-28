"""Application entry point for JSON Pretty Diff."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from infrastructure.cli import JsonPrettyDiffCLI


def main() -> int:
    """Runs the JSON Pretty Diff command-line interface."""

    cli = JsonPrettyDiffCLI()
    return cli.run()


if __name__ == "__main__":
    raise SystemExit(main())
