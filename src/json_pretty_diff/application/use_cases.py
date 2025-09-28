"""Application use cases for JSON Pretty Diff."""

from typing import Any, Dict

from ..domain.models import DiffResult
from ..domain.services import compute_top_level_diff

class DiffUseCase:
    """Application service that orchestrates diff computation."""

    def execute(self, source: Dict[str, Any], target: Dict[str, Any]) -> DiffResult:
        """Generates the diff result for two JSON objects."""

        return compute_top_level_diff(source, target)
