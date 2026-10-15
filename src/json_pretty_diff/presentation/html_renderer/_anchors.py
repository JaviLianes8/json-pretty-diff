"""Anchor utilities for the HTML renderer."""

from __future__ import annotations

from typing import Dict


def sanitize_anchor(key: str, used: Dict[str, int]) -> str:
    """Creates a safe and unique anchor identifier for the given key."""

    base = "".join(ch if ch.isalnum() else "-" for ch in key).strip("-") or "key"
    index = used.get(base, 0)
    anchor = f"{base}-{index + 1}" if index else base
    # A numbered anchor can equal the plain anchor of another key ("a b" and "a-b" give
    # "a-b-2", which is also the anchor of "a-b-2"); skip numbers that are already taken.
    while index and anchor in used:
        index += 1
        anchor = f"{base}-{index + 1}"
    used[base] = index + 1
    if anchor != base:
        used.setdefault(anchor, 1)
    return anchor


__all__ = ["sanitize_anchor"]
