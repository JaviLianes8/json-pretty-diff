"""Domain models for JSON Pretty Diff."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass(frozen=True)
class DiffResult:
    """Represents the comparison outcome between two JSON documents."""

    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        """Indicates whether the diff contains any change."""

        return bool(self.added or self.removed or self.changed)
