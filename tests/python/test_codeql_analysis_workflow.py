"""CodeQL fails a language that has no source code, so the matrix must follow the repository.

The workflow used a fixed python/javascript/go matrix, so every repository without
all three languages got failing jobs.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.utils.fake_runner import ActionResult, run_workflow_step
from tests.utils.fakebin import make_fakebin

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/codeql-analysis.yml"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Requires Bash (Linux/WSL)")


def _load() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _detect(tmp_path: Path, requested: str, languages: dict[str, int]) -> ActionResult:
    fakebin = make_fakebin(tmp_path, {"gh": f"echo '{json.dumps(languages)}'"})
    return run_workflow_step(
        WORKFLOW,
        "languages",
        "Detect languages",
        context={"github.token": "token", "inputs.languages": requested},
        env={"PATH": f"{fakebin}:{os.environ['PATH']}", "GITHUB_REPOSITORY": "owner/repo"},
        workdir=tmp_path,
    )


def test_the_matrix_comes_from_the_detected_languages() -> None:
    analyze = _load()["jobs"]["analyze"]

    assert analyze["needs"] == "languages"
    assert analyze["if"] == "needs.languages.outputs.count != '0'"
    assert analyze["strategy"]["matrix"]["language"] == (
        "${{ fromJson(needs.languages.outputs.languages) }}"
    )


def test_compiled_languages_are_autobuilt() -> None:
    init = next(
        step for step in _load()["jobs"]["analyze"]["steps"]
        if step.get("uses", "").startswith("github/codeql-action/init@")
    )

    assert "'autobuild' || 'none'" in init["with"]["build-mode"]
    for language in ("c-cpp", "csharp", "go", "java-kotlin"):
        assert f'"{language}"' in init["with"]["build-mode"]


@posix_only
def test_languages_are_detected_from_the_repository(tmp_path: Path) -> None:
    result = _detect(
        tmp_path, "", {"Python": 900, "TypeScript": 40, "JavaScript": 5, "HTML": 3, "Swift": 1}
    )

    assert result.code == 0, result.stderr
    assert json.loads(result.outputs["languages"]) == ["javascript-typescript", "python"]
    assert result.outputs["count"] == "2"


@posix_only
def test_requested_languages_are_used_as_given(tmp_path: Path) -> None:
    result = _detect(tmp_path, '["go"]', {"Python": 1})

    assert result.code == 0, result.stderr
    assert json.loads(result.outputs["languages"]) == ["go"]


@posix_only
@pytest.mark.parametrize("requested", ['"python"', "[1]"])
def test_malformed_language_lists_are_rejected(tmp_path: Path, requested: str) -> None:
    assert _detect(tmp_path, requested, {}).code != 0


@posix_only
def test_a_repository_without_codeql_languages_skips_analysis(tmp_path: Path) -> None:
    result = _detect(tmp_path, "", {"Shell": 10, "HCL": 5})

    assert result.code == 0, result.stderr
    assert result.outputs["count"] == "0"
