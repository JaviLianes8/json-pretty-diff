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

It runs `ruff format --check`, `ruff check`, `mypy --strict` and `pytest` (which also runs
the examples in the docstrings). The installed wheel test is slower and opt-in: set
`JSON_PRETTY_DIFF_E2E=1` before `pytest`.

## Compatibility

The command-line options, the exit codes, the names in `json_pretty_diff.__all__` and the HTML
report are public. `tests/golden/` holds reports rendered by 1.1.1; `tests/golden_changes.py`
spells out, as an edit, every way the current report differs from them, and the tests check
that nothing else does (only the generation time is masked). A change to the report is a
change of the format and needs its own discussion first.
