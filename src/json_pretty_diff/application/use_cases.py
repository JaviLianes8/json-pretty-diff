"""Application use cases for JSON Pretty Diff."""

from typing import Any, Mapping

from ..domain.models import DiffResult
from ..domain.services import compute_top_level_diff


class DiffUseCase:
    """Application service that orchestrates diff computation.

    >>> from json_pretty_diff import DiffUseCase
    >>> DiffUseCase().execute({"a": 1}, {"a": 2}).changed
    {'a': {'old': 1, 'new': 2}}
    """

    def execute(self, source: Mapping[str, Any], target: Mapping[str, Any]) -> DiffResult:
        """Generates the diff result for two JSON objects."""

        return compute_top_level_diff(source, target)
