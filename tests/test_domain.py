"""The top-level comparison and the JSON value equality it relies on."""

from __future__ import annotations

import math
from typing import Any, Callable

import pytest

from json_pretty_diff.application.use_cases import DiffUseCase
from json_pretty_diff.domain._equality import json_equal
from json_pretty_diff.domain.services import compute_top_level_diff

NAN = float("nan")


def test_keys_are_split_into_added_removed_and_changed_in_sorted_order() -> None:
    diff = compute_top_level_diff(
        {"b": 1, "a": 1, "keep": [1], "z": 0, "y": 0},
        {"keep": [1], "z": 1, "y": 2, "d": 4, "c": 3},
    )
    assert diff.added == ["c", "d"]
    assert diff.removed == ["a", "b"]
    assert list(diff.changed) == ["y", "z"]
    assert diff.changed["z"] == {"old": 0, "new": 1}
    assert diff.added_values == {"c": 3, "d": 4}
    assert diff.removed_values == {"a": 1, "b": 1}
    assert diff.has_differences


def test_identical_objects_have_no_differences() -> None:
    diff = compute_top_level_diff({"a": {"b": [1, 2]}}, {"a": {"b": [1, 2]}})
    assert (diff.added, diff.removed, diff.changed) == ([], [], {})
    assert not diff.has_differences


@pytest.mark.parametrize(
    ("source", "target"),
    [({"a": 1}, {}), ({}, {"a": 1}), ({"a": 1}, {"a": 2})],
)
def test_any_single_difference_counts(source: dict[str, Any], target: dict[str, Any]) -> None:
    assert compute_top_level_diff(source, target).has_differences


def test_snapshots_are_copies_of_the_inputs() -> None:
    source: dict[str, Any] = {"a": {"b": [1]}}
    target: dict[str, Any] = {"a": {"b": [2]}}
    diff = compute_top_level_diff(source, target)
    source["a"]["b"].append(9)
    target["a"]["b"].append(9)
    assert diff.source_snapshot == {"a": {"b": [1]}}
    assert diff.target_snapshot == {"a": {"b": [2]}}


def test_use_case_delegates_to_the_service() -> None:
    diff = DiffUseCase().execute({"a": 1}, {"a": 1, "b": 2})
    assert diff.added == ["b"]
    assert diff.added_values == {"b": 2}


@pytest.mark.parametrize(
    ("source", "target"),
    [(True, 1), (False, 0), (1, True), (0.0, False), ([False], [0]), ({"x": True}, {"x": 1})],
)
def test_booleans_never_equal_numbers(source: Any, target: Any) -> None:
    assert not json_equal(source, target)
    diff = compute_top_level_diff({"k": source}, {"k": target})
    assert diff.changed == {"k": {"old": source, "new": target}}


@pytest.mark.parametrize(
    "make",
    [lambda: float("nan"), lambda: [float("nan")], lambda: {"x": [1, float("nan")]}],
)
def test_nan_equals_nan(make: Callable[[], Any]) -> None:
    left, right = make(), make()
    assert json_equal(left, right)
    assert not compute_top_level_diff({"k": left}, {"k": right}).has_differences


def test_nan_differs_from_numbers_and_infinity() -> None:
    assert not json_equal(NAN, 1.0)
    assert not json_equal(1.0, NAN)
    assert not json_equal(NAN, math.inf)
    assert not json_equal(NAN, None)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (1, 1.0, True),
        (True, True, True),
        (False, True, False),
        (None, None, True),
        (None, 0, False),
        ("1", 1, False),
        (1.5, 1.5, True),
        (1.5, 2.5, False),
        (-0.0, 0.0, True),
        ([1, 2], [1, 2], True),
        ([1, 2], [2, 1], False),
        ([1, 2], [1, 2, 3], False),
        ([1], (1,), False),
        ((1, True), (1, True), True),
        ((1, True), (1, 1), False),
        ({"a": 1, "b": 2}, {"b": 2, "a": 1}, True),
        ({"a": 1}, {"a": 1, "b": 1}, False),
        ({"a": 1}, {"b": 1}, False),
        ({"a": 1}, [("a", 1)], False),
        ([], {}, False),
        ({"a": [{"b": True}]}, {"a": [{"b": True}]}, True),
        ({"a": [{"b": True}]}, {"a": [{"b": 1}]}, False),
    ],
)
def test_json_equality(left: Any, right: Any, expected: bool) -> None:
    assert json_equal(left, right) is expected
    assert json_equal(right, left) is expected
