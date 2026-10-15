"""Reading inputs and writing the report and status lines to any stream."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from conftest import write_bytes

from json_pretty_diff.infrastructure._io import (
    InputOutputError,
    load_json_object,
    write_line,
    write_report,
    write_report_to_stream,
)


def _stream(encoding: str, newline: str | None = None) -> tuple[io.BytesIO, io.TextIOWrapper]:
    raw = io.BytesIO()
    return raw, io.TextIOWrapper(raw, encoding=encoding, newline=newline)


def test_report_goes_out_as_utf8_and_the_stream_is_restored() -> None:
    raw, stream = _stream("cp1252", newline="\r\n")
    write_report_to_stream("é ❤\n", stream)
    assert raw.getvalue() == "é ❤\r\n".encode()
    assert (stream.encoding, stream.errors) == ("cp1252", "strict")
    stream.write("é")
    stream.flush()
    assert raw.getvalue().endswith(b"\xe9")


def test_lone_surrogate_in_the_report_becomes_an_escape() -> None:
    raw, stream = _stream("utf-8")
    write_report_to_stream("a\ud800b", stream)
    assert raw.getvalue() == b"a\\ud800b"


def test_streams_without_reconfigure_get_the_text_as_is() -> None:
    stream = io.StringIO()
    write_report_to_stream("é ❤\n", stream)
    assert stream.getvalue() == "é ❤\n"


def test_status_line_escapes_what_the_stream_cannot_encode() -> None:
    raw, stream = _stream("ascii", newline="\n")
    write_line("saved to ñ.html\n", stream)
    stream.flush()
    assert raw.getvalue() == b"saved to \\xf1.html\n"
    write_line("plain\n", stream)
    stream.flush()
    assert raw.getvalue().endswith(b"plain\n")


def test_load_returns_the_object(tmp_path: Path) -> None:
    path = write_bytes(tmp_path / "a.json", b'{"a": [1, true, null]}')
    assert load_json_object(path) == {"a": [1, True, None]}


def test_load_errors_carry_the_message(tmp_path: Path) -> None:
    with pytest.raises(InputOutputError, match="must be a JSON object"):
        load_json_object(write_bytes(tmp_path / "a.json", b"null"))


def test_write_creates_folders_and_writes_utf8(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b.html"
    write_report(target, "ñ\ud800")
    assert target.read_bytes().startswith("ñ".encode())
    assert target.read_text(encoding="utf-8").endswith("\\ud800")


def test_other_read_errors_carry_the_system_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = write_bytes(tmp_path / "a.json", b"{}")

    def refuse(self: Path) -> bytes:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "read_bytes", refuse)
    with pytest.raises(InputOutputError, match=r"^Cannot read .*a\.json: Permission denied$"):
        load_json_object(path)
