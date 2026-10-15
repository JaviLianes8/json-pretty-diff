"""Standard output and error for the command line: a reader that goes away ends output quietly."""

from __future__ import annotations

import errno
import os
import sys
from typing import Callable

from ._io import InputOutputError, write_line

# Windows reports a closed pipe as EINVAL on flush rather than EPIPE.
_READER_GONE = (errno.EPIPE, errno.EINVAL)


def to_stdout(write: Callable[[], None]) -> bool:
    """Runs ``write`` against standard output.

    Returns ``False`` when the reader closed the pipe (``jpd a.json b.json | head``): the
    rest of the output is dropped without a traceback. Any other failure becomes an
    :class:`InputOutputError`.
    """

    try:
        write()
        sys.stdout.flush()
    except OSError as error:
        if isinstance(error, BrokenPipeError) or error.errno in _READER_GONE:
            _discard_stdout()
            return False
        reason = error.strerror or error
        raise InputOutputError(f"Cannot write to standard output: {reason}") from error
    return True


def _discard_stdout() -> None:
    """Points the stdout descriptor at the null device so the exit flush cannot fail."""

    try:
        null = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(null, sys.stdout.fileno())
        finally:
            os.close(null)
    except (OSError, ValueError, AttributeError):
        pass


def to_stderr(prefix: str, message: str) -> None:
    """Writes ``prefix: message`` to standard error; a closed stderr is ignored."""

    try:
        write_line(f"{prefix}: {message}\n", sys.stderr)
        sys.stderr.flush()
    except OSError:
        pass


__all__ = ["to_stderr", "to_stdout"]
