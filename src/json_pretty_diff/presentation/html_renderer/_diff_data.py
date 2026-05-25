"""Data preparation utilities for diff rendering."""

from __future__ import annotations

import json
from difflib import unified_diff
from typing import Any, Dict, Iterable, List, Tuple

from ...domain.models import DiffResult

MISSING = object()

def truncate_text(value: str, limit: int = 10_000) -> Tuple[str, bool]:
    """Truncates long text values returning the cut string and a flag."""

    if len(value) <= limit:
        return value, False
    return value[:limit], True

def serialize_for_diff(value: Any) -> str:
    """Serializes arbitrary data structures so that they can be diffed."""

    try:
        return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(value)

def prepare_serialized_for_diff(value: Any) -> Tuple[str, bool, str]:
    """Provides serialized and truncated representations for diff rendering."""

    if value is MISSING:
        return "", False, ""
    serialized = serialize_for_diff(value)
    truncated, was_truncated = truncate_text(serialized)
    return truncated, was_truncated, serialized

def diff_lines(old: Iterable[str], new: Iterable[str]) -> List[str]:
    """Computes a unified diff for the provided iterables of lines."""

    return list(
        unified_diff(
            list(old),
            list(new),
            fromfile="old",
            tofile="new",
            lineterm="",
        )
    )

def build_git_entries(diff: DiffResult, anchors: Dict[str, str]) -> List[Dict[str, Any]]:
    """Builds ordered entries that describe the diff payload for each key."""

    entries: List[Dict[str, Any]] = []

    for key in diff.added:
        entries.append(
            {
                "key": key,
                "anchor": anchors[key],
                "status": "added",
                "old": MISSING,
                "new": diff.added_values.get(key, MISSING),
            }
        )

    for key in diff.removed:
        entries.append(
            {
                "key": key,
                "anchor": anchors[key],
                "status": "removed",
                "old": diff.removed_values.get(key, MISSING),
                "new": MISSING,
            }
        )

    for key in sorted(diff.changed):
        entries.append(
            {
                "key": key,
                "anchor": anchors[key],
                "status": "changed",
                "old": diff.changed[key]["old"],
                "new": diff.changed[key]["new"],
            }
        )

    return entries


__all__ = [
    "MISSING",
    "build_git_entries",
    "diff_lines",
    "prepare_serialized_for_diff",
    "serialize_for_diff",
    "truncate_text",
]
