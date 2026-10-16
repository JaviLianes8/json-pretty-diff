"""Domain models for JSON Pretty Diff."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class DiffResult:
    """Represents the comparison outcome between two JSON documents.

    ``added`` and ``removed`` are sorted key lists, ``changed`` maps each key whose value
    differs to ``{"old": ..., "new": ...}``, ``added_values`` and ``removed_values`` hold the
    values of the added and removed keys, and the two snapshots are copies of the compared
    objects.

    >>> from json_pretty_diff import DiffResult
    >>> DiffResult().has_differences
    False
    >>> DiffResult(added=["a"], added_values={"a": 1}).has_differences
    True
    """

    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    added_values: Dict[str, Any] = field(default_factory=dict)
    removed_values: Dict[str, Any] = field(default_factory=dict)
    source_snapshot: Dict[str, Any] = field(default_factory=dict)
    target_snapshot: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        """Indicates whether the diff contains any change."""

        return bool(self.added or self.removed or self.changed)
