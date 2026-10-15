"""The jpd command in a fresh interpreter: console encodings, stack depth, the source script."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from conftest import FIXTURES, ROOT, write_bytes

BASE = FIXTURES / "base.json"
UPDATE = FIXTURES / "update.json"
_MAIN = "from json_pretty_diff.cli import main; raise SystemExit(main())"


def _nested(path: Path, depth: int, extra: bytes = b"") -> Path:
    return write_bytes(path, b'{"a": ' + b"[" * depth + b"]" * depth + extra + b"}")


def test_a_shared_key_450_levels_deep_is_compared(tmp_path: Path) -> None:
    # 1.1.1 compares this depth on every supported Python; a fresh interpreter keeps
    # pytest's own stack out of the count.
    source = _nested(tmp_path / "p.json", 450)
    target = _nested(tmp_path / "q.json", 450, b', "b": 1')
    result = _run_process("-c", _MAIN, str(source), str(target), "-q", encoding="utf-8")
    assert result.returncode == 1, result.stderr
    assert result.stderr == b""


def test_too_deep_for_the_report_is_an_error_not_a_traceback(tmp_path: Path) -> None:
    deep = _nested(tmp_path / "deep.json", 900)
    result = _run_process("-c", _MAIN, str(deep), str(BASE), "-q", encoding="utf-8")
    assert result.returncode == 2
    assert result.stderr.decode().startswith("Error: ")
    assert b"Traceback" not in result.stderr


def _run_process(*args: str, encoding: str) -> subprocess.CompletedProcess[bytes]:
    # Windows refuses variables over 32767 characters; a parent shell may hold one.
    env = {key: value for key, value in os.environ.items() if len(value) < 32767}
    env.update(PYTHONIOENCODING=encoding, PYTHONPATH=str(ROOT / "src"))
    env.pop("PYTHONUTF8", None)
    return subprocess.run([sys.executable, *args], capture_output=True, env=env, check=False)


def test_redirected_stdout_is_utf8_whatever_the_console_encoding() -> None:
    result = _run_process("-c", _MAIN, str(BASE), str(UPDATE), encoding="cp1252")
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
