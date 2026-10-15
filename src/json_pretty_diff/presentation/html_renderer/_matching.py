"""Line matching for the diff blocks and the full JSON table, bounded in time.

``difflib.SequenceMatcher`` can take time growing with the square of the input: an array of
16,000 values repeating 150 numbers took about two minutes in 1.1.1. The matcher here is ``difflib``'s own, counting the steps of its inner loop; when the
count passes a budget, the part between the lines both sides share at the start and at the
end is reported as one replacement. Below the budget the result is exactly ``difflib``'s.
"""

from __future__ import annotations

from difflib import Match, SequenceMatcher
from typing import Iterator, List, Literal, Optional, Sequence, Tuple

Tag = Literal["replace", "delete", "insert", "equal"]
Opcode = Tuple[Tag, int, int, int, int]

# Inner-loop steps allowed for one matching: about three seconds of work at worst. A shuffled
# array of 100,000 numbers needs about 5 million and stays below it.
STEP_BUDGET = 10_000_000


class _OverBudget(Exception):
    """The matching would take more steps than the budget allows."""


class _BoundedMatcher(SequenceMatcher):  # type: ignore[type-arg]
    """``SequenceMatcher(None, old, new)`` that stops once its budget is spent."""

    def __init__(self, old: Sequence[str], new: Sequence[str], budget: int) -> None:
        super().__init__(None, old, new)
        self._old, self._new = old, new
        # steps[i]: the cost of scanning old[:i], one step per line and per position of
        # that line in ``new`` (the lists the inner loop of find_longest_match walks).
        positions = getattr(self, "b2j")  # noqa: B009 (not in the type stubs)
        steps = [0]
        for line in old:
            steps.append(steps[-1] + 1 + len(positions.get(line, ())))
        self._steps = steps
        self._left = budget
        self._plain: Optional[List[Opcode]] = None

    def find_longest_match(
        self, alo: int = 0, ahi: Optional[int] = None, blo: int = 0, bhi: Optional[int] = None
    ) -> Match:
        top = len(self._old) if ahi is None else ahi
        self._left -= self._steps[top] - self._steps[alo]
        if self._left < 0:
            raise _OverBudget
        return super().find_longest_match(alo, top, blo, len(self._new) if bhi is None else bhi)

    def get_opcodes(self) -> List[Opcode]:
        if self._plain is None:
            try:
                return super().get_opcodes()
            except _OverBudget:
                self._plain = plain_opcodes(self._old, self._new)
        return self._plain


def plain_opcodes(old: Sequence[str], new: Sequence[str]) -> List[Opcode]:
    """Opcodes keeping the shared start and end and replacing everything in between."""

    limit = min(len(old), len(new))
    start = 0
    while start < limit and old[start] == new[start]:
        start += 1
    end = 0
    while end < limit - start and old[-1 - end] == new[-1 - end]:
        end += 1
    old_stop, new_stop = len(old) - end, len(new) - end
    codes: List[Opcode] = []
    if start:
        codes.append(("equal", 0, start, 0, start))
    if start < old_stop and start < new_stop:
        codes.append(("replace", start, old_stop, start, new_stop))
    elif start < old_stop:
        codes.append(("delete", start, old_stop, start, new_stop))
    elif start < new_stop:
        codes.append(("insert", start, old_stop, start, new_stop))
    if end:
        codes.append(("equal", old_stop, len(old), new_stop, len(new)))
    return codes


def line_opcodes(old: List[str], new: List[str], budget: int = STEP_BUDGET) -> List[Opcode]:
    """``SequenceMatcher(None, old, new).get_opcodes()``, bounded in time."""

    return list(_BoundedMatcher(old, new, budget).get_opcodes())


def unified_lines(old: List[str], new: List[str], budget: int = STEP_BUDGET) -> Iterator[str]:
    """``difflib.unified_diff(old, new, "old", "new", lineterm="")``, bounded in time."""

    started = False
    for group in _BoundedMatcher(old, new, budget).get_grouped_opcodes(3):
        if not started:
            started = True
            yield "--- old"
            yield "+++ new"
        yield f"@@ -{_range(group[0][1], group[-1][2])} +{_range(group[0][3], group[-1][4])} @@"
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                yield from (" " + line for line in old[i1:i2])
                continue
            yield from ("-" + line for line in old[i1:i2])
            yield from ("+" + line for line in new[j1:j2])


def _range(start: int, stop: int) -> str:
    """A hunk range as ``difflib`` writes it: ``3``, ``3,4`` or ``2,0``."""

    length = stop - start
    if length == 1:
        return str(start + 1)
    return f"{start + 1 if length else start},{length}"


__all__ = ["STEP_BUDGET", "line_opcodes", "plain_opcodes", "unified_lines"]
