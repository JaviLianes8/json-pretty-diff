"""Domain services for computing JSON diffs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from ._equality import json_equal
from .models import DiffResult


def compute_top_level_diff(source: Dict[str, Any], target: Dict[str, Any]) -> DiffResult:
    """Computes the top-level diff between two JSON objects.

    Keys are compared at the top level only; a key counts as changed when its two values are
    different JSON values at any depth. ``true`` differs from ``1``, ``NaN`` equals ``NaN``,
    and ``1`` equals ``1.0``.

    >>> from json_pretty_diff import compute_top_level_diff
    >>> diff = compute_top_level_diff({"a": 1, "b": True, "c": 1}, {"a": 1.0, "b": 1, "d": 2})
    >>> diff.added, diff.removed, diff.changed
    (['d'], ['c'], {'b': {'old': True, 'new': 1}})
    """

    added_keys = sorted(set(target) - set(source))
    removed_keys = sorted(set(source) - set(target))
    shared_keys = set(source) & set(target)

    added_values = {key: target[key] for key in added_keys}
    removed_values = {key: source[key] for key in removed_keys}

    changed: Dict[str, Dict[str, Any]] = {}
    for key in sorted(shared_keys):
        if not json_equal(source[key], target[key]):
            changed[key] = {"old": source[key], "new": target[key]}

    return DiffResult(
        added=added_keys,
        removed=removed_keys,
        changed=changed,
        added_values=added_values,
        removed_values=removed_values,
        source_snapshot=deepcopy(source),
        target_snapshot=deepcopy(target),
    )
