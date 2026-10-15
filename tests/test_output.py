"""Standard output: a closed pipe ends quietly, other failures are errors; --no-timestamp."""

from __future__ import annotations

import errno
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import FIXTURES, ROOT, run_cli

from json_pretty_diff.infrastructure import _output
from json_pretty_diff.infrastructure import cli as cli_module
from json_pretty_diff.infrastructure._io import InputOutputError
from json_pretty_diff.infrastructure._output import to_stderr, to_stdout

BASE = FIXTURES / "base.json"
UPDATE = FIXTURES / "update.json"
Capture = pytest.CaptureFixture[str]


@pytest.fixture(autouse=True)
def discarded(monkeypatch: pytest.MonkeyPatch) -> list[bool]:
    """Record instead of pointing this process's stdout at the null device."""
    calls: list[bool] = []
    monkeypatch.setattr(_output, "_discard_stdout", lambda: calls.append(True))
    return calls


def _raising(error: OSError) -> Callable[..., None]:
    def write(*args: Any, **kwargs: Any) -> None:
        raise error

    return write


@pytest.mark.parametrize(
    "error", [BrokenPipeError(errno.EPIPE, "Broken pipe"), OSError(errno.EINVAL, "Invalid")]
)
def test_a_closed_pipe_is_not_an_error(error: OSError, discarded: list[bool]) -> None:
    assert to_stdout(_raising(error)) is False
    assert discarded == [True]


def test_other_write_failures_are_errors() -> None:
    with pytest.raises(InputOutputError, match=r"^Cannot write to standard output: No space$"):
        to_stdout(_raising(OSError(errno.ENOSPC, "No space")))
    assert to_stdout(lambda: None) is True


def test_a_closed_stderr_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    class Closed(io.StringIO):
        def write(self, text: str) -> int:
            raise BrokenPipeError(errno.EPIPE, "Broken pipe")

    monkeypatch.setattr(sys, "stderr", Closed())
    to_stderr("Warning", "ignored")


@pytest.mark.parametrize("error", [BrokenPipeError(errno.EPIPE, "x"), OSError(errno.EINVAL, "x")])
def test_report_to_a_closed_pipe_keeps_the_exit_code(
    error: OSError, monkeypatch: pytest.MonkeyPatch, capsys: Capture
) -> None:
    monkeypatch.setattr(cli_module, "write_report_to_stream", _raising(error))
    assert run_cli(BASE, UPDATE) == 1
    assert run_cli(BASE, BASE) == 0
    assert capsys.readouterr().err == ""


def test_status_line_to_a_closed_pipe_keeps_the_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capture
) -> None:
    monkeypatch.setattr(cli_module, "write_line", _raising(BrokenPipeError(errno.EPIPE, "x")))
    assert run_cli(BASE, UPDATE, "-o", tmp_path / "r.html") == 1
    assert (tmp_path / "r.html").is_file()
    assert capsys.readouterr().err == ""


def test_a_full_disk_on_stdout_is_an_error(
    monkeypatch: pytest.MonkeyPatch, capsys: Capture
) -> None:
    monkeypatch.setattr(
        cli_module, "write_report_to_stream", _raising(OSError(errno.ENOSPC, "Full"))
    )
    assert run_cli(BASE, UPDATE) == 2
    assert capsys.readouterr().err == "Error: Cannot write to standard output: Full\n"


def test_a_reader_that_stops_early_gets_no_traceback(tmp_path: Path) -> None:
    big = {f"key{i}": "value " * 20 for i in range(4000)}
    source = tmp_path / "s.json"
    source.write_text(json.dumps(big), encoding="utf-8")
    code = "from json_pretty_diff.cli import main; raise SystemExit(main())"
    env = {"PYTHONPATH": str(ROOT / "src"), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(source), str(BASE)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert process.stdout is not None and process.stderr is not None
    assert process.stdout.read(15) == b"<!DOCTYPE html>"
    process.stdout.close()
    stderr = process.stderr.read()
    assert process.wait(timeout=120) == 1
    assert stderr == b""


def test_a_status_line_to_a_closed_pipe_leaves_nothing_for_the_exit_flush(
    tmp_path: Path,
) -> None:
    # The pipe is closed before jpd writes its short status line, which sits in the buffer
    # until a flush; without the flush and the null device swap the interpreter's own flush
    # at exit fails and prints "Exception ignored".
    code = "from json_pretty_diff.cli import main; raise SystemExit(main())"
    env = {"PYTHONPATH": str(ROOT / "src"), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(BASE), str(UPDATE), "-o", str(tmp_path / "r.html")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert process.stdout is not None and process.stderr is not None
    process.stdout.close()
    stderr = process.stderr.read()
    assert process.wait(timeout=120) == 1
    assert stderr == b""
    assert (tmp_path / "r.html").is_file()


def test_no_timestamp_gives_the_same_bytes_every_time(tmp_path: Path, capsys: Capture) -> None:
    first, second = tmp_path / "1.html", tmp_path / "2.html"
    assert run_cli(BASE, UPDATE, "--no-timestamp", "-q", "-o", first) == 1
    assert run_cli(BASE, UPDATE, "--no-timestamp", "-q", "-o", second) == 1
    page = first.read_text(encoding="utf-8")
    assert first.read_bytes() == second.read_bytes()
    assert "Generated on" not in page
    assert '<p style="color: #64748b; font-size: 0.9rem;">json-pretty-diff v' in page
    assert run_cli(BASE, UPDATE, "-q", "-o", first) == 1
    assert "Generated on " in first.read_text(encoding="utf-8")


def test_no_standard_output_is_an_error_and_the_file_report_still_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Capture
) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    assert run_cli(BASE, UPDATE) == 2
    assert capsys.readouterr().err == "Error: Cannot write to standard output: there is none\n"
    assert run_cli(BASE, UPDATE, "-o", tmp_path / "r.html") == 1
    assert (tmp_path / "r.html").is_file()
    monkeypatch.setattr(sys, "stderr", None)
    assert run_cli(BASE, UPDATE) == 2
