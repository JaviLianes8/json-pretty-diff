"""Behaviour checked against RFC 8259 as fetched by scripts/fetch_upstream.py.

The RFC is not part of the repository (see tests/upstream/MANIFEST.json); these tests skip
while it is absent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from conftest import FIXTURES, run_cli, upstream, write_bytes

from json_pretty_diff.domain._equality import json_equal
from json_pretty_diff.domain.services import compute_top_level_diff

RFC = "rfc8259.txt"
Capture = pytest.CaptureFixture[str]


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def section(text: str, start: str, end: str) -> str:
    body = text[text.index(start) :]
    return body[: body.index(end)]


def examples() -> list[str]:
    """The JSON texts of section 13, cut out of the fetched RFC."""
    text = section(upstream(RFC), "\n13.  Examples", "\n14.  References")
    text = re.sub(
        r"\n\f?\n*Bray +Standards Track +\[Page \d+\]\n\f?\nRFC 8259 +JSON +December 2017\n",
        "\n",
        text,
    )
    obj = section(text, "This is a JSON object:", "Its Image member")
    array = section(text, "This is a JSON array containing two objects:", "Here are three")
    values = text[text.index("containing only values:") :].splitlines()[1:]
    obj = obj.split(":", 1)[1]
    array = array.split(":", 1)[1]
    return [obj, array, *[line.strip() for line in values if line.strip()]]


def test_the_object_example_has_no_differences_with_itself() -> None:
    obj = json.loads(examples()[0])
    assert obj["Image"]["IDs"] == [116, 943, 234, 38793]
    assert not compute_top_level_diff(obj, json.loads(examples()[0])).has_differences


def test_the_object_example_with_a_boolean_turned_into_zero_is_changed() -> None:
    # Section 3 lists false, true and numbers as separate kinds of value.
    assert "value = false / null / true / object / array / number / string" in flat(upstream(RFC))
    obj = json.loads(examples()[0])
    other = json.loads(examples()[0])
    other["Image"]["Animated"] = 0
    assert obj["Image"]["Animated"] is False
    assert list(compute_top_level_diff(obj, other).changed) == ["Image"]


@pytest.mark.parametrize("index", [1, 2, 3, 4])
def test_examples_whose_root_is_not_an_object_are_rejected(
    index: int, tmp_path: Path, capsys: Capture
) -> None:
    texts = examples()
    assert texts[2:] == ['"Hello world!"', "42", "true"]
    path = write_bytes(tmp_path / "e.json", texts[index].encode())
    assert run_cli(path, FIXTURES / "base.json") == 2
    assert capsys.readouterr().err.endswith("must be a JSON object.\n")


def test_byte_order_mark_may_be_ignored(tmp_path: Path, capsys: Capture) -> None:
    text = flat(upstream(RFC))
    assert (
        "implementations that parse JSON texts MAY ignore the presence of a byte order mark" in text
    )
    path = write_bytes(tmp_path / "e.json", b"\xef\xbb\xbf" + examples()[0].encode())
    assert run_cli(path, path, "-q") == 0


def test_json_text_is_utf8(tmp_path: Path, capsys: Capture) -> None:
    assert "MUST be encoded using UTF-8" in flat(upstream(RFC))
    path = write_bytes(
        tmp_path / "e.json", examples()[0].replace("Floor", "Fl\xf6or").encode("latin-1")
    )
    assert run_cli(path, path) == 2
    assert "not UTF-8 text" in capsys.readouterr().err


def test_object_names_should_be_unique_and_the_last_one_is_read(
    tmp_path: Path, capsys: Capture
) -> None:
    # Section 4: names SHOULD be unique; with duplicates, Python's reader keeps the last one.
    text = flat(upstream(RFC))
    assert "The names within an object SHOULD be unique." in text
    assert "Many implementations report the last name/value pair only." in text
    path = write_bytes(tmp_path / "d.json", b'{"a": 1, "a": 2}')
    other = write_bytes(tmp_path / "o.json", b'{"a": 2}')
    assert run_cli(path, other, "-q") == 0
    assert run_cli(path, other, "-o", tmp_path / "r.html") == 0
    assert capsys.readouterr().err == (
        f"Warning: {path} repeats names inside an object, the last value is used "
        '(RFC 8259 section 4): "a"\n'
    )


def test_nan_and_infinity_are_not_permitted_and_get_a_warning(
    tmp_path: Path, capsys: Capture
) -> None:
    # Section 6 excludes them from the number grammar; jpd still compares, with a warning.
    assert "(such as Infinity and NaN) are not permitted." in flat(upstream(RFC))
    path = write_bytes(tmp_path / "n.json", b'{"a": NaN, "b": Infinity, "c": -Infinity}')
    assert run_cli(path, path, "-o", tmp_path / "r.html") == 0
    err = capsys.readouterr().err
    assert err.startswith(f"Warning: {path} holds values RFC 8259 does not allow (section 6)")
    assert err.endswith(": NaN, Infinity, -Infinity\n")


def test_numbers_beyond_binary64_are_compared_as_infinity_with_a_warning(
    tmp_path: Path, capsys: Capture
) -> None:
    # Section 6 lets implementations limit range and precision, pointing at IEEE 754 binary64.
    text = flat(upstream(RFC))
    assert "allows implementations to set limits on the range and precision of numbers" in text
    assert "IEEE 754 binary64 (double precision)" in text
    big = write_bytes(tmp_path / "b.json", b'{"a": 1e400}')
    bigger = write_bytes(tmp_path / "c.json", b'{"a": 2e400}')
    assert run_cli(big, bigger, "-o", tmp_path / "r.html") == 0
    assert capsys.readouterr().err.count("beyond the range of a double") == 2


def test_literal_names_are_distinct_from_each_other_and_from_numbers() -> None:
    text = flat(upstream(RFC))
    assert "The literal names MUST be lowercase." in text
    literals = [json.loads(name) for name in ("false", "null", "true", "0", "1")]
    for i, left in enumerate(literals):
        for j, right in enumerate(literals):
            assert json_equal(left, right) is (i == j)
