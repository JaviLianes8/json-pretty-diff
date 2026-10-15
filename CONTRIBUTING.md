# Contributing

Issues and pull requests are welcome. Everything runs locally; there is no hosted CI.

## Setup

```bash
pip install -e .
pip install -r requirements-dev.txt
python scripts/fetch_upstream.py   # optional: RFC 8259 for tests/test_sources.py
```

The fetch script downloads the reference files listed in `tests/upstream/MANIFEST.json` and
checks their size and sha256. They are not part of the repository, and the tests that read
them skip while they are missing.

## Quality gate

Run before every commit:

```powershell
./scripts/check.ps1
```

It runs `ruff format --check`, `ruff check`, `mypy --strict` and `pytest`. The installed
wheel test is slower and opt-in: set `JSON_PRETTY_DIFF_E2E=1` before `pytest`.

## Compatibility

The command-line options, the exit codes and the HTML report are public. The report is
pinned byte for byte by `tests/golden/` (only the generation time is masked); a change to
the report is a change of the format and needs its own discussion first.
