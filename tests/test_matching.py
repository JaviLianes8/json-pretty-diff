"""Line matching: difflib's result below the budget, a plain replacement past it, bounded time."""

from __future__ import annotations

import difflib
import random
import time
from typing import List, Sequence

import pytest

from json_pretty_diff import compute_top_level_diff, render_html
from json_pretty_diff.presentation.html_renderer._matching import (
    STEP_BUDGET,
    line_opcodes,
    plain_opcodes,
    unified_lines,
)


def _texts(rng: random.Random) -> tuple[List[str], List[str]]:
    alphabet = [f"line {i}\n" for i in range(rng.choice([2, 5, 30]))]
    old = [rng.choice(alphabet) for _ in range(rng.randrange(0, 60))]
    new = list(old)
    for _ in range(rng.randrange(0, 8)):
        if new and rng.random() < 0.5:
            del new[rng.randrange(len(new))]
        else:
            new.insert(rng.randrange(len(new) + 1), rng.choice(alphabet))
    if new and rng.random() < 0.3:
        new[-1] = new[-1].rstrip("\n")
    return old, new


def _apply(old: List[str], new: List[str], codes: Sequence[tuple[str, int, int, int, int]]) -> None:
    rebuilt: List[str] = []
    position = 0
    for tag, i1, i2, j1, j2 in codes:
        assert i1 == position and tag in {"equal", "replace", "delete", "insert"}
        rebuilt.extend(old[i1:i2] if tag == "equal" else new[j1:j2])
        if tag == "equal":
            assert old[i1:i2] == new[j1:j2]
        position = i2
    assert position == len(old) and rebuilt == new


def test_below_the_budget_the_result_is_difflibs() -> None:
    rng = random.Random(8259)
    for _ in range(400):
        old, new = _texts(rng)
        expected = list(difflib.unified_diff(old, new, "old", "new", lineterm=""))
        assert list(unified_lines(old, new)) == expected
        assert line_opcodes(old, new) == difflib.SequenceMatcher(None, old, new).get_opcodes()


def test_past_the_budget_the_middle_is_replaced_and_the_text_rebuilds() -> None:
    rng = random.Random(4627)
    for _ in range(400):
        old, new = _texts(rng)
        codes = line_opcodes(old, new, budget=0)
        assert codes == plain_opcodes(old, new)
        assert [tag for tag, *_ in codes].count("equal") <= 2
        _apply(old, new, codes)
        patch = list(unified_lines(old, new, budget=0))
        assert patch[:2] == (["--- old", "+++ new"] if old != new else [])
        kept = [line[1:] for line in patch[2:] if line[:1] in " +"]
        assert "".join(kept) in "".join(new)


@pytest.mark.parametrize(
    ("old", "new", "codes"),
    [
        ([], [], []),
        (["a"], ["a"], [("equal", 0, 1, 0, 1)]),
        (
            ["a", "b", "c"],
            ["a", "x", "c"],
            [("equal", 0, 1, 0, 1), ("replace", 1, 2, 1, 2), ("equal", 2, 3, 2, 3)],
        ),
        (["a", "b"], ["a"], [("equal", 0, 1, 0, 1), ("delete", 1, 2, 1, 1)]),
        (["b"], ["a", "b"], [("insert", 0, 0, 0, 1), ("equal", 0, 1, 1, 2)]),
        (["a", "a"], ["a", "a", "a"], [("equal", 0, 2, 0, 2), ("insert", 2, 2, 2, 3)]),
    ],
)
def test_plain_opcodes_keep_the_shared_start_and_end(
    old: List[str], new: List[str], codes: list[tuple[str, int, int, int, int]]
) -> None:
    assert plain_opcodes(old, new) == codes


def test_hunk_ranges_are_written_like_difflib() -> None:
    assert list(unified_lines(["a\n"], [], budget=0)) == [
        "--- old",
        "+++ new",
        "@@ -1 +0,0 @@",
        "-a\n",
    ]
    assert list(unified_lines([], ["a\n", "b\n"], budget=0))[2] == "@@ -0,0 +1,2 @@"


@pytest.mark.parametrize("size", [16_000, 100_000])
def test_shuffled_and_repetitive_arrays_render_in_bounded_time(size: int) -> None:
    # 1.1.1 took over a minute on the 16,000-value array and minutes on the shuffled one.
    repetitive = ([i % 150 for i in range(16_000)], [(i * 7) % 150 for i in range(16_000)])
    shuffled = (list(range(size)), [(i * 7919) % size for i in range(size)])
    for old, new in (repetitive, shuffled):
        start = time.perf_counter()
        page = render_html(compute_top_level_diff({"x": old}, {"x": new}))
        assert time.perf_counter() - start < 30
        assert page.endswith("</html>")
    assert STEP_BUDGET == 3_000_000
