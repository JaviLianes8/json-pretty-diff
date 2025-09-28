"""Domain services for computing JSON diffs."""

from copy import deepcopy
from typing import Any, Dict

from .models import DiffResult

def compute_top_level_diff(source: Dict[str, Any], target: Dict[str, Any]) -> DiffResult:
    """Computes the top-level diff between two JSON objects."""

    added_keys = sorted(set(target) - set(source))
    removed_keys = sorted(set(source) - set(target))
    shared_keys = set(source) & set(target)

    added_values = {key: target[key] for key in added_keys}
    removed_values = {key: source[key] for key in removed_keys}

    changed = {}
    for key in sorted(shared_keys):
        if source[key] != target[key]:
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
