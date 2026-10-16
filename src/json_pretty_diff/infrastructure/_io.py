"""Reading the input files and writing the report for the command line."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from ._decode import decode_json

_UTF16_MARKS = (b"\xff\xfe", b"\xfe\xff")
_UTF32_MARKS = (b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")
# Paths quoted in messages are cut to this many characters.
_PATH_LIMIT = 1000


def shown_path(path: object) -> str:
    """A path as messages show it, cut so a huge argument never floods the console."""

    text = str(path)
    return text if len(text) <= _PATH_LIMIT else text[:_PATH_LIMIT] + "..."


class InputOutputError(Exception):
    """A file could not be read or written; the message follows ``Error:``."""


def load_json_object(path: Path, warnings: Optional[List[str]] = None) -> Dict[str, Any]:
    """Reads a UTF-8 JSON file whose root is an object.

    What the file holds that RFC 8259 does not allow or advises against (``NaN``, numbers
    beyond a double, repeated names) is read as Python reads it and, when ``warnings`` is
    given, described there, one message per kind, each starting with the path.
    """

    name = shown_path(path)
    if path.is_dir():
        raise InputOutputError(f"Cannot read {name}: it is a directory")
    try:
        raw = path.read_bytes()
    except FileNotFoundError as error:
        raise InputOutputError(f"File not found: {name}") from error
    except OSError as error:
        raise InputOutputError(f"Cannot read {name}: {error.strerror or error}") from error

    try:
        # RFC 8259 section 8.1: JSON is UTF-8 and a parser may ignore a byte order mark.
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        hint = ""
        if raw[:4] in _UTF32_MARKS:
            hint = " (it looks like UTF-32)"
        elif raw[:2] in _UTF16_MARKS:
            hint = " (it looks like UTF-16)"
        message = f"Invalid JSON in {name}: not UTF-8 text (byte {error.start}){hint}"
        raise InputOutputError(message) from error

    try:
        data, notes = decode_json(text)
    except json.JSONDecodeError as error:
        raise InputOutputError(f"Invalid JSON in {name}: {error.msg}") from error
    except RecursionError as error:
        raise InputOutputError(f"Invalid JSON in {name}: nested too deeply") from error
    except ValueError as error:
        # Integers longer than the interpreter's digit limit (Python 3.11 and later).
        message = f"Invalid JSON in {name}: an integer has more digits than Python reads"
        raise InputOutputError(message) from error

    if not isinstance(data, dict):
        raise InputOutputError(f"The root element of {name} must be a JSON object.")
    if warnings is not None:
        warnings.extend(f"{name} {note}" for note in notes)
    return data


def write_report(path: Path, html_report: str) -> None:
    """Writes the report as UTF-8, creating the parent folders."""

    name = shown_path(path)
    if path.is_dir():
        raise InputOutputError(f"Cannot write {name}: it is a directory")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Lone surrogates from "\udXXX" escapes cannot be UTF-8; keep them visible as escapes.
        path.write_text(html_report, encoding="utf-8", errors="backslashreplace")
    except OSError as error:
        raise InputOutputError(f"Cannot write {name}: {error.strerror or error}") from error


def write_report_to_stream(html_report: str, stream: Optional[TextIO] = None) -> None:
    """Writes the report to stdout as UTF-8, the charset its ``<meta>`` declares.

    A redirected stdout on Windows uses the console code page, which cannot encode most of
    the page. The stream is switched to UTF-8 for the report and switched back afterwards;
    its newline handling is left as it is.
    """

    target = sys.stdout if stream is None else stream
    reconfigure = getattr(target, "reconfigure", None)
    if reconfigure is None:
        target.write(html_report)
        return
    encoding, errors = target.encoding, target.errors
    reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        target.write(html_report)
    finally:
        reconfigure(encoding=encoding, errors=errors)


def write_line(text: str, stream: Optional[TextIO] = None) -> None:
    """Writes a status line, escaping what the stream's encoding cannot represent."""

    target = sys.stdout if stream is None else stream
    try:
        target.write(text)
    except UnicodeEncodeError:
        encoding = target.encoding or "utf-8"
        target.write(text.encode(encoding, "backslashreplace").decode(encoding))


__all__ = [
    "InputOutputError",
    "load_json_object",
    "shown_path",
    "write_line",
    "write_report",
    "write_report_to_stream",
]
