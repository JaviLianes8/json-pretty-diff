"""Application entry point for JSON Pretty Diff."""

from json_pretty_diff.cli import main as cli_main


def main() -> int:
    """Runs the JSON Pretty Diff command-line interface."""

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
