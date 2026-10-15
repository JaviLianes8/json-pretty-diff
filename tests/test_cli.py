"""The jpd command: exit codes, output targets, and documented errors instead of tracebacks."""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

import pytest
from conftest import FIXTURES, ROOT, run_cli, write_bytes, write_json

from json_pretty_diff.application.use_cases import DiffUseCase

BASE = FIXTURES / "base.json"
UPDATE = FIXTURES / "update.json"
Capture = pytest.CaptureFixture[str]


def test_differences_exit_with_one_and_html_goes_to_stdout(capsys: Capture) -> None:
    assert run_cli(BASE, UPDATE) == 1
    out = capsys.readouterr().out
    assert out.startswith("<!DOCTYPE html>") and out.endswith("</html>\n")


def test_no_differences_exit_with_zero(capsys: Capture) -> None:
    assert run_cli(BASE, BASE) == 0
    assert "No differences." in capsys.readouterr().out


def test_output_file_is_written_and_summarised(tmp_path: Path, capsys: Capture) -> None:
    target = tmp_path / "nested" / "dir" / "diff.html"
    assert run_cli(BASE, UPDATE, "-o", target) == 1
    assert target.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    assert capsys.readouterr().out == f"Report saved to {target} (2 added, 1 removed, 5 changed)\n"


def test_output_file_without_differences(tmp_path: Path, capsys: Capture) -> None:
    assert run_cli(BASE, BASE, "--output", tmp_path / "d.html") == 0
    assert capsys.readouterr().out.endswith("(no differences)\n")


def test_quiet_prints_nothing(tmp_path: Path, capsys: Capture) -> None:
    assert run_cli(BASE, UPDATE, "-q") == 1
    assert run_cli(BASE, UPDATE, "--quiet", "-o", tmp_path / "d.html") == 1
    assert capsys.readouterr() == ("", "")
    assert (tmp_path / "d.html").is_file()


def test_no_style_reaches_the_report(capsys: Capture) -> None:
    run_cli(BASE, UPDATE, "--no-style")
    assert "<style>" not in capsys.readouterr().out


def test_open_requires_an_output_file(capsys: Capture) -> None:
    assert run_cli(BASE, UPDATE, "--open") == 2
    assert capsys.readouterr().err == "Error: --open requires -o/--output to be specified.\n"


def test_open_launches_the_browser_on_the_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []
    monkeypatch.setattr(webbrowser, "open", opened.append)
    target = tmp_path / "d.html"
    assert run_cli(BASE, UPDATE, "-o", target, "--open", "-q") == 1
    assert opened == [target.resolve().as_uri()]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"{", "Invalid JSON in {path}: Expecting property name enclosed in double quotes"),
        (b"[1, 2]", "The root element of {path} must be a JSON object."),
        (b'"text"', "The root element of {path} must be a JSON object."),
        (b'{"a": "\xff"}', "Invalid JSON in {path}: not UTF-8 text (byte 7)"),
        (b"\xff\xfe{\x00}\x00", "Invalid JSON in {path}: not UTF-8 text (byte 0)"),
        (b"[" * 100_000, "Invalid JSON in {path}: nested too deeply"),
    ],
    ids=["syntax", "array-root", "string-root", "bad-utf8", "utf16", "too-deep"],
)
def test_bad_input_is_an_error_with_exit_two(
    tmp_path: Path, capsys: Capture, content: bytes, message: str
) -> None:
    bad = write_bytes(tmp_path / "bad.json", content)
    assert run_cli(bad, BASE) == 2
    captured = capsys.readouterr()
    assert captured.err == f"Error: {message.format(path=bad)}\n"
    assert captured.out == ""


def test_missing_file(tmp_path: Path, capsys: Capture) -> None:
    missing = tmp_path / "missing.json"
    assert run_cli(BASE, missing) == 2
    assert capsys.readouterr().err == f"Error: File not found: {missing}\n"


def test_unreadable_input_is_an_error(tmp_path: Path, capsys: Capture) -> None:
    assert run_cli(tmp_path, BASE) == 2
    assert capsys.readouterr().err.startswith(f"Error: Cannot read {tmp_path}: ")


def test_unwritable_output_is_an_error(tmp_path: Path, capsys: Capture) -> None:
    assert run_cli(BASE, UPDATE, "-o", tmp_path) == 2
    assert capsys.readouterr().err.startswith(f"Error: Cannot write {tmp_path}: ")
    blocker = write_bytes(tmp_path / "file", b"")
    assert run_cli(BASE, UPDATE, "-o", blocker / "d.html") == 2


@pytest.mark.skipif(not hasattr(sys, "set_int_max_str_digits"), reason="no digit limit")
def test_integer_beyond_the_digit_limit_is_an_error(tmp_path: Path, capsys: Capture) -> None:
    big = write_bytes(tmp_path / "big.json", b'{"a": ' + b"9" * 5000 + b"}")
    assert run_cli(big, BASE) == 2
    assert capsys.readouterr().err.startswith(f"Error: Invalid JSON in {big}: ")


def test_byte_order_mark_is_accepted(tmp_path: Path, capsys: Capture) -> None:
    bom = write_bytes(tmp_path / "bom.json", b"\xef\xbb\xbf" + BASE.read_bytes())
    assert run_cli(bom, BASE) == 0
    assert capsys.readouterr().err == ""


def test_too_deep_to_compare_is_an_error(
    tmp_path: Path, capsys: Capture, monkeypatch: pytest.MonkeyPatch
) -> None:
    def deep(self: DiffUseCase, source: Any, target: Any) -> Any:
        raise RecursionError

    monkeypatch.setattr(DiffUseCase, "execute", deep)
    assert run_cli(BASE, UPDATE) == 2
    assert (
        capsys.readouterr().err == f"Error: {BASE} or {UPDATE} is nested too deeply to compare.\n"
    )


def test_deep_but_readable_documents_never_end_in_a_traceback(tmp_path: Path) -> None:
    depth = 900
    deep = write_bytes(tmp_path / "deep.json", b'{"a": ' + b"[" * depth + b"]" * depth + b"}")
    assert run_cli(deep, BASE, "-q") in (1, 2)


def test_lone_surrogate_is_written_as_an_escape(tmp_path: Path) -> None:
    source = write_bytes(tmp_path / "s.json", b'{"a": "\\ud800"}')
    target = tmp_path / "d.html"
    assert run_cli(source, BASE, "-q", "-o", target) == 1
    assert "\\ud800" in target.read_text(encoding="utf-8")


def _run_process(*args: str, encoding: str) -> subprocess.CompletedProcess[bytes]:
    # Windows refuses variables over 32767 characters; a parent shell may hold one.
    env = {key: value for key, value in os.environ.items() if len(value) < 32767}
    env.update(PYTHONIOENCODING=encoding, PYTHONPATH=str(ROOT / "src"))
    env.pop("PYTHONUTF8", None)
    return subprocess.run([sys.executable, *args], capture_output=True, env=env, check=False)


def test_redirected_stdout_is_utf8_whatever_the_console_encoding() -> None:
    code = "from json_pretty_diff.cli import main; raise SystemExit(main())"
    result = _run_process("-c", code, str(BASE), str(UPDATE), encoding="cp1252")
    assert result.returncode == 1, result.stderr
    report = result.stdout.decode("utf-8")
    assert "García" in report and "https://example.com/ñ" in report
    assert report.replace("\r\n", "\n").endswith("</html>\n")


def test_main_script_runs_from_a_source_checkout(tmp_path: Path) -> None:
    target = tmp_path / "d.html"
    result = _run_process(
        str(ROOT / "main.py"), str(BASE), str(BASE), "-o", str(target), encoding="utf-8"
    )
    assert result.returncode == 0, result.stderr
    assert target.is_file()


def test_sample_documents_are_objects(tmp_path: Path) -> None:
    assert (
        run_cli(write_json(tmp_path / "a.json", {}), write_json(tmp_path / "b.json", {}), "-q") == 0
    )
