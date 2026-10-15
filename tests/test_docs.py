"""README and GUIDE: every Python example runs, and the documented behaviour is what jpd does."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from conftest import ROOT, run_cli, write_bytes

Capture = pytest.CaptureFixture[str]
DOCS = ["README.md", "GUIDE.md"]


def _blocks(name: str, language: str) -> list[str]:
    text = (ROOT / name).read_text(encoding="utf-8")
    return re.findall(rf"```{language}\n(.*?)```", text, re.S)


@pytest.mark.parametrize("name", DOCS)
def test_python_examples_run(name: str) -> None:
    blocks = _blocks(name, "python")
    assert blocks
    for block in blocks:
        exec(compile(block, name, "exec"), {})


def _table_rows() -> list[tuple[str, str, str]]:
    text = (ROOT / "GUIDE.md").read_text(encoding="utf-8")
    table = text[text.index("| Old | New | Result |") :].split("\n\n", 1)[0]
    rows = re.findall(r"^\| `([^`]*)` \| `([^`]*)` \| (\w+)", table, re.M)
    assert len(rows) == 10
    return rows


@pytest.mark.parametrize(("old", "new", "result"), _table_rows())
def test_the_comparison_table_is_what_jpd_does(
    old: str, new: str, result: str, tmp_path: Path
) -> None:
    source = write_bytes(tmp_path / "s.json", f'{{"k": {old}}}'.encode())
    target = write_bytes(tmp_path / "t.json", f'{{"k": {new}}}'.encode())
    assert run_cli(source, target, "-q") == {"equal": 0, "changed": 1}[result]


def test_the_warning_lines_in_the_guide_are_what_jpd_prints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capture
) -> None:
    monkeypatch.chdir(tmp_path)
    write_bytes(tmp_path / "data.json", b'{"id": 1, "id": 2, "a": NaN, "b": 1e400}')
    assert run_cli("data.json", "data.json", "-o", "r.html") == 0
    printed = capsys.readouterr().err.splitlines()
    shown = _blocks("GUIDE.md", "text")[0].splitlines()
    assert printed == shown


def test_every_option_is_documented_in_both_files(capsys: Capture) -> None:
    assert run_cli("--help") == 0
    options = set(re.findall(r"(?<![\w-])--[a-z][a-z-]+", capsys.readouterr().out)) - {"--help"}
    assert "--no-timestamp" in options
    for name in DOCS:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert {
            option for option in options if f"`{option}" not in text and option not in text
        } == set()
