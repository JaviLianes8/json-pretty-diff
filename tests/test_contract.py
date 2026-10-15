"""The public surface of 1.1.1 is pinned: names, signatures, options and packaging."""

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


def test_package_exports_only_the_version() -> None:
    assert json_pretty_diff.__all__ == ["__version__"]


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
    assert list(render) == ["diff", "include_styles"]
    assert render["include_styles"].kind is inspect.Parameter.KEYWORD_ONLY
    assert render["include_styles"].default is True
    run = inspect.signature(JsonPrettyDiffCLI.run).parameters
    assert list(run) == ["self", "argv"]
    assert run["argv"].default is None
    assert list(inspect.signature(DiffUseCase.execute).parameters) == ["self", "source", "target"]


@pytest.mark.parametrize(
    "option", ["-o", "--output", "--open", "-q", "--quiet", "--no-style", "--version"]
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
