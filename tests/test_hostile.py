"""Hostile Python input and page content: cycles, control characters, types, long paths."""

from __future__ import annotations

import json
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

import pytest
from conftest import FIXTURES, run_cli, write_bytes

from json_pretty_diff import compute_top_level_diff, render_html
from json_pretty_diff.domain._equality import json_equal
from json_pretty_diff.presentation.html_renderer._full_json_script import (
    render_full_json_filter_script,
)

Capture = pytest.CaptureFixture[str]


def _within(seconds: float, work: Any) -> Any:
    """Run ``work`` in a thread and fail if it has not finished in time."""
    result: list[Any] = []
    thread = threading.Thread(target=lambda: result.append(work()), daemon=True)
    thread.start()
    thread.join(seconds)
    assert not thread.is_alive(), "did not finish"
    return result[0]


def _cyclic_dict() -> dict[str, Any]:
    value: dict[str, Any] = {}
    value["x"] = value
    return value


def _cyclic_list() -> list[Any]:
    value: list[Any] = []
    value.append(value)
    return value


@pytest.mark.parametrize("make", [_cyclic_dict, _cyclic_list])
def test_cyclic_structures_compare_and_render_without_hanging(make: Any) -> None:
    assert _within(10, lambda: json_equal(make(), make())) is True
    diff = _within(10, lambda: compute_top_level_diff({"k": make()}, {"k": make()}))
    assert not diff.has_differences
    changed = _within(10, lambda: compute_top_level_diff({"k": make()}, {"k": [1]}))
    assert list(changed.changed) == ["k"]
    assert _within(10, lambda: render_html(changed)).endswith("</html>")


def test_control_characters_never_reach_the_page_raw() -> None:
    page = render_html(compute_top_level_diff({"\x00nul\x1b\x7f": 1}, {}), warnings=["\x01w"])
    assert not [c for c in page if (ord(c) < 32 and c not in "\t\n\r") or c == "\x7f"]
    assert "\\u0000nul\\u001b\\u007f" in page and "\\u0001w" in page


def test_long_paths_are_cut_in_error_messages(tmp_path: Path, capsys: Capture) -> None:
    long = tmp_path / ("x" * 150) / ("y" * 150) / "missing.json"
    assert run_cli(long, FIXTURES / "base.json") == 2
    err = capsys.readouterr().err
    assert err == f"Error: File not found: {str(long)[:200]}...\n"


def test_utf32_input_gets_its_own_hint(tmp_path: Path, capsys: Capture) -> None:
    path = write_bytes(tmp_path / "u.json", '{"a": 2}'.encode("utf-32"))
    assert run_cli(path, FIXTURES / "base.json") == 2
    assert capsys.readouterr().err.endswith("(it looks like UTF-32)\n")


@pytest.mark.parametrize(
    ("source", "target", "message"),
    [
        ({1: 1}, {}, "source keys must be strings"),
        ({}, {"a": 1, 2: 2}, "target keys must be strings"),
    ],
)
def test_keys_must_be_strings(source: Any, target: Any, message: str) -> None:
    with pytest.raises(TypeError, match=f"^{message}"):
        compute_top_level_diff(source, target)


@pytest.mark.parametrize("warnings", ["abc", [1], ["ok", None], None])
def test_warnings_must_be_strings(warnings: Any) -> None:
    with pytest.raises(TypeError, match=r"^warnings must be a sequence of strings$"):
        render_html(compute_top_level_diff({}, {}), warnings=warnings)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_search_highlights_the_typed_text_where_lowercasing_changes_length(
    tmp_path: Path,
) -> None:
    script = render_full_json_filter_script("t")
    start = script.index("    function escapeHtml(")
    body = script[start : script.index("    function ensureMatchVisible(")]
    cases = [['"İİİİ<b>key</b>"', "key"], ["aXa xa", "XA"], ["a.b a+b", "a+b"], ["no", "zz"]]
    code = (
        body
        + f"console.log(JSON.stringify({json.dumps(cases)}.map(c => highlightText(c[0], c[1]))));"
    )
    (tmp_path / "s.js").write_text(code, encoding="utf-8")
    out = subprocess.run(
        ["node", str(tmp_path / "s.js")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    mark = '<mark class="full-json-highlight">'
    assert json.loads(out.stdout) == [
        f"&quot;İİİİ&lt;b&gt;{mark}key</mark>&lt;/b&gt;&quot;",
        f"a{mark}Xa</mark> {mark}xa</mark>",
        f"a.b {mark}a+b</mark>",
        "no",
    ]
