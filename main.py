"""Application entry point for JSON Pretty Diff."""

from importlib import util
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

if "jpd" not in sys.modules:
    spec = util.spec_from_file_location("jpd", SRC_PATH / "__init__.py")
    if spec and spec.loader:
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.__path__ = [str(SRC_PATH)]
        sys.modules["jpd"] = module

from jpd.infrastructure.cli import JsonPrettyDiffCLI


def main() -> int:
    """Runs the JSON Pretty Diff command-line interface."""

    cli = JsonPrettyDiffCLI()
    return cli.run()


if __name__ == "__main__":
    raise SystemExit(main())
