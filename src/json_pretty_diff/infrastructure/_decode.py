"""Decoding JSON text while noting what RFC 8259 does not allow or advises against."""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Set, Tuple

# A finding names at most this many examples; the rest are counted.
_SHOWN = 5
# Names and numbers quoted in a warning are cut to this many characters.
_QUOTE_LIMIT = 40


def _quote(text: str) -> str:
    """Shows a name or number in a warning, cut so a huge input never floods the message."""

    if len(text) > _QUOTE_LIMIT:
        text = text[:_QUOTE_LIMIT] + "..."
    return text


class _Finding:
    """The distinct examples of one kind of finding, in order of appearance."""

    def __init__(self) -> None:
        self.seen: Set[str] = set()
        self.shown: List[str] = []

    def add(self, text: str) -> None:
        if text not in self.seen:
            self.seen.add(text)
            if len(self.shown) < _SHOWN:
                self.shown.append(text)

    def listing(self) -> str:
        more = len(self.seen) - len(self.shown)
        return ", ".join(self.shown) + (f" and {more} more" if more else "")


class _Reader:
    """The hooks handed to ``json.loads``; each one records what it meets."""

    def __init__(self) -> None:
        self.constants = _Finding()
        self.overflows = _Finding()
        self.duplicates = _Finding()

    def constant(self, name: str) -> float:
        self.constants.add(name)
        return float(name)

    def number(self, text: str) -> float:
        value = float(text)
        if math.isinf(value):
            self.overflows.add(_quote(text))
        return value

    def members(self, pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
        members = dict(pairs)
        if len(members) != len(pairs):
            names: Set[str] = set()
            for name, _ in pairs:
                if name in names:
                    self.duplicates.add(_quote(json.dumps(name, ensure_ascii=False)))
                names.add(name)
        return members

    def notes(self) -> List[str]:
        notes: List[str] = []
        if self.constants.seen:
            notes.append(
                "holds values RFC 8259 does not allow (section 6), read and compared as "
                f"numbers: {self.constants.listing()}"
            )
        if self.overflows.seen:
            notes.append(
                "holds numbers beyond the range of a double, read and compared as "
                f"infinity: {self.overflows.listing()}"
            )
        if self.duplicates.seen:
            notes.append(
                "repeats names inside an object, the last value is used (RFC 8259 "
                f"section 4): {self.duplicates.listing()}"
            )
        return notes


def decode_json(text: str) -> Tuple[Any, List[str]]:
    """Decodes JSON text as ``json.loads`` does and lists what deserves a warning.

    The value is the one ``json.loads`` returns: ``NaN`` and ``Infinity`` are read as floats,
    a number beyond the range of a double as infinity, and a repeated name keeps its last
    value. Each note says which of these the text holds; the caller adds the file name.
    """

    reader = _Reader()
    data = json.loads(
        text,
        parse_constant=reader.constant,
        parse_float=reader.number,
        object_pairs_hook=reader.members,
    )
    return data, reader.notes()


__all__ = ["decode_json"]
