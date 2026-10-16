"""Equality of decoded JSON values."""

from __future__ import annotations

import math
from typing import Any, List, Set, Tuple

_PLAIN = (str, int, type(None))


def json_equal(left: Any, right: Any) -> bool:
    """Tells whether two decoded JSON values are the same JSON value.

    Python's ``==`` says ``True == 1`` and ``nan != nan``. In JSON ``true`` and ``1`` are
    different value types (RFC 8259 section 3), and a ``NaN`` token read twice is the same
    token. Containers are compared member by member so that the rule holds at any depth;
    everything else keeps Python's equality (``1`` and ``1.0`` stay equal).

    The walk uses its own stack, so it accepts any depth the rest of the report can handle.
    """

    pending: List[Tuple[Any, Any]] = [(left, right)]
    # Container pairs already expanded: a cyclic structure (only possible from Python, never
    # from a file) is compared once per pair instead of forever.
    expanded: Set[Tuple[int, int]] = set()
    while pending:
        a, b = pending.pop()
        if isinstance(a, (dict, list, tuple)) and isinstance(b, (dict, list, tuple)):
            pair = (id(a), id(b))
            if pair in expanded:
                continue
            expanded.add(pair)
        if a is b or (type(a) is type(b) and type(a) in _PLAIN):
            if a is not b and a != b:
                return False
        elif isinstance(a, bool) or isinstance(b, bool):
            if not (isinstance(a, bool) and isinstance(b, bool) and a == b):
                return False
        elif isinstance(a, float) and isinstance(b, float):
            if not (a == b or (math.isnan(a) and math.isnan(b))):
                return False
        elif isinstance(a, dict) and isinstance(b, dict):
            if a.keys() != b.keys():
                return False
            pending.extend((value, b[key]) for key, value in a.items())
        elif isinstance(a, (list, tuple)) and type(a) is type(b):
            if len(a) != len(b):
                return False
            pending.extend(zip(a, b))
        elif not a == b:
            return False
    return True


__all__ = ["json_equal"]
