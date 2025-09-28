"""Anchor utilities for the HTML renderer."""

from __future__ import annotations

from typing import Dict

def sanitize_anchor(key: str, used: Dict[str, int]) -> str:
    """Creates a safe and unique anchor identifier for the given key."""

    base = "".join(ch if ch.isalnum() else "-" for ch in key).strip("-") or "key"
    index = used.get(base, 0)
    if index:
        anchor = f"{base}-{index + 1}"
    else:
        anchor = base
    used[base] = index + 1
    return anchor

__all__ = ["sanitize_anchor"]
