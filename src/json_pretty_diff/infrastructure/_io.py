"""Reading the input files and writing the report for the command line."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, TextIO


class InputOutputError(Exception):
    """A file could not be read or written; the message follows ``Error:``."""


def load_json_object(path: Path) -> Dict[str, Any]:
    """Reads a UTF-8 JSON file whose root is an object."""

    try:
        raw = path.read_bytes()
    except FileNotFoundError as error:
        raise InputOutputError(f"File not found: {path}") from error
    except OSError as error:
        raise InputOutputError(f"Cannot read {path}: {error.strerror or error}") from error

    try:
        # RFC 8259 section 8.1: JSON is UTF-8 and a parser may ignore a byte order mark.
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        message = f"Invalid JSON in {path}: not UTF-8 text (byte {error.start})"
        raise InputOutputError(message) from error

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise InputOutputError(f"Invalid JSON in {path}: {error.msg}") from error
    except RecursionError as error:
        raise InputOutputError(f"Invalid JSON in {path}: nested too deeply") from error
    except ValueError as error:
        # Integers longer than the interpreter's digit limit (Python 3.11 and later).
        raise InputOutputError(f"Invalid JSON in {path}: {error}") from error

    if not isinstance(data, dict):
        raise InputOutputError(f"The root element of {path} must be a JSON object.")
    return data


def write_report(path: Path, html_report: str) -> None:
    """Writes the report as UTF-8, creating the parent folders."""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Lone surrogates from "\udXXX" escapes cannot be UTF-8; keep them visible as escapes.
        path.write_text(html_report, encoding="utf-8", errors="backslashreplace")
    except OSError as error:
        raise InputOutputError(f"Cannot write {path}: {error.strerror or error}") from error


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
        target.flush()
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
    "write_line",
    "write_report",
    "write_report_to_stream",
]
