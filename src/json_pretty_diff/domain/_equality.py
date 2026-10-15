"""Equality of decoded JSON values."""

from __future__ import annotations

import math
from typing import Any


def json_equal(left: Any, right: Any) -> bool:
    """Tells whether two decoded JSON values are the same JSON value.

    Python's ``==`` says ``True == 1`` and ``nan != nan``. In JSON ``true`` and ``1`` are
    different value types (RFC 8259 section 3), and a ``NaN`` token read twice is the same
    token. Containers are compared member by member so that the rule holds at any depth;
    everything else keeps Python's equality (``1`` and ``1.0`` stay equal).
    """

    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, float) and isinstance(right, float):
        return left == right or (math.isnan(left) and math.isnan(right))
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return False
        return all(json_equal(value, right[key]) for key, value in left.items())
    if isinstance(left, (list, tuple)) and type(left) is type(right):
        if len(left) != len(right):
            return False
        return all(json_equal(a, b) for a, b in zip(left, right))
    result: bool = left == right
    return result


__all__ = ["json_equal"]
