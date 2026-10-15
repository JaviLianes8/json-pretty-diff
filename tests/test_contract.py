"""The public surface is pinned: names, signatures, options and packaging.

Every name and option of 1.1.1 is still there; 1.2.0 adds the top-level names, two keyword
options of ``render_html`` and ``--no-timestamp``.
"""

from __future__ import annotations

import dataclasses
import inspect
import re

import pytest
from conftest import ROOT, run_cli

import json_pretty_diff
from json_pretty_diff import cli
from json_pretty_diff.application.use_cases import DiffUseCase
from json_pretty_diff.domain.models import DiffResult
from json_pretty_diff.domain.services import compute_top_level_diff
from json_pretty_diff.infrastructure.cli import JsonPrettyDiffCLI
from json_pretty_diff.presentation.html_renderer import render_html

PUBLIC = {
    "DiffResult": DiffResult,
    "DiffUseCase": DiffUseCase,
    "JsonPrettyDiffCLI": JsonPrettyDiffCLI,
    "compute_top_level_diff": compute_top_level_diff,
    "main": cli.main,
    "render_html": render_html,
}


def test_package_exports_exactly_the_public_names() -> None:
    assert sorted(json_pretty_diff.__all__) == sorted([*PUBLIC, "__version__"])
    for name, value in PUBLIC.items():
        assert getattr(json_pretty_diff, name) is value
    public = {name for name in vars(json_pretty_diff) if not name.startswith("_")}
    assert public - set(PUBLIC) <= {
        "application",
        "cli",
        "domain",
        "infrastructure",
        "presentation",
        "version",
    }


@pytest.mark.parametrize("name", sorted(PUBLIC))
def test_every_public_name_has_a_docstring_with_an_example(name: str) -> None:
    doc = inspect.getdoc(PUBLIC[name]) or ""
    assert ">>> " in doc, name


def test_version_is_three_numbers_and_matches_the_project_file() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", json_pretty_diff.__version__)
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{json_pretty_diff.__version__}"' in project


def test_console_script_points_at_cli_main() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'jpd = "json_pretty_diff.cli:main"' in project
    assert set(cli.__all__) == {"main", "JsonPrettyDiffCLI"}
    assert cli.JsonPrettyDiffCLI is JsonPrettyDiffCLI
    assert callable(cli.main)


def test_py_typed_ships_with_the_package() -> None:
    package = ROOT / "src" / "json_pretty_diff"
    assert (package / "py.typed").is_file()
    assert '"py.typed"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_diff_result_fields_are_unchanged() -> None:
    names = [field.name for field in dataclasses.fields(DiffResult)]
    assert names == [
        "added",
        "removed",
        "changed",
        "added_values",
        "removed_values",
        "source_snapshot",
        "target_snapshot",
    ]
    assert DiffResult().has_differences is False
    with pytest.raises(dataclasses.FrozenInstanceError):
        DiffResult().added = []  # type: ignore[misc]


def test_function_signatures_are_unchanged() -> None:
    assert list(inspect.signature(compute_top_level_diff).parameters) == ["source", "target"]
    render = inspect.signature(render_html).parameters
    assert list(render) == ["diff", "include_styles", "include_timestamp", "warnings"]
    for option, default in (("include_styles", True), ("include_timestamp", True)):
        assert render[option].kind is inspect.Parameter.KEYWORD_ONLY
        assert render[option].default is default
    assert render["warnings"].kind is inspect.Parameter.KEYWORD_ONLY
    assert render["warnings"].default == ()
    run = inspect.signature(JsonPrettyDiffCLI.run).parameters
    assert list(run) == ["self", "argv"]
    assert run["argv"].default is None
    assert list(inspect.signature(DiffUseCase.execute).parameters) == ["self", "source", "target"]


@pytest.mark.parametrize(
    "option",
    ["-o", "--output", "--open", "-q", "--quiet", "--no-style", "--no-timestamp", "--version"],
)
def test_every_documented_option_is_in_the_help(
    option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_cli("--help") == 0
    assert re.search(rf"(^|[\s,]){re.escape(option)}\b", capsys.readouterr().out, re.M)


def test_version_option_prints_the_program_and_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run_cli("--version") == 0
    assert capsys.readouterr().out.strip() == f"jpd {json_pretty_diff.__version__}"


def test_missing_arguments_exit_with_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_cli() == 2
    assert "usage: jpd" in capsys.readouterr().err
