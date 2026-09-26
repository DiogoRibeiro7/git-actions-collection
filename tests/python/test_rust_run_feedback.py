"""The Rust gate workflows annotate problems in the diff and summarize results on the run page."""

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
import yaml

from tests.utils.rust_steps import (
    BROKEN_DOC_LINK_LIB,
    COMPILE_ERROR_LIB,
    FAILING_TEST_LIB,
    LIB_CLIPPY_WARNING,
    UNFORMATTED_LIB,
    require_rust_tools,
    run_step,
    write_crate,
)

WORKFLOWS = Path(".github/workflows")
GATES = {
    "rust-ci.yml": ("build", {"format", "check", "clippy", "tests"}),
    "rust-quality.yml": ("quality", {"format", "clippy"}),
    "rust-docs.yml": ("docs", {"docs"}),
}
CLIPPY_RETURN = "title=clippy%3A%3Aneedless_return::"
posix_only = pytest.mark.skipif(os.name != "posix", reason="Fake runner requires bash (Linux CI)")


def _steps(workflow: str) -> list[dict[str, Any]]:
    data = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))
    return data["jobs"][GATES[workflow][0]]["steps"]


def _script(workflow: str) -> str:
    setup = next(step for step in _steps(workflow) if step.get("name") == "Set up run feedback")
    return setup["run"].split("<<'PY'\n", 1)[1].rsplit("PY\n", 1)[0]


def _run_script(
    tmp_path: Path, *args: str, stdin: str = "", env: dict[str, str] | None = None
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    """Run the script from a crate directory under a fake checkout at tmp_path."""
    script = tmp_path / "rust_feedback.py"
    script.write_text(_script("rust-ci.yml"), encoding="utf-8")
    output = tmp_path / "github_output"
    output.write_text("", encoding="utf-8")
    crate = tmp_path / "crate"
    crate.mkdir(exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        input=stdin,
        cwd=crate,
        env={
            **os.environ,
            "GITHUB_OUTPUT": str(output),
            "GITHUB_WORKSPACE": str(tmp_path),
            **(env or {}),
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    outputs = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
    return proc, outputs


def _compiler_message(
    level: str, message: str, code: str | None, file_name: str, line: int,
    expansion: dict[str, Any] | None = None,
) -> str:
    span = {
        "file_name": file_name, "line_start": line, "line_end": line,
        "column_start": 5, "column_end": 17, "is_primary": True, "expansion": expansion,
    }
    return json.dumps({
        "reason": "compiler-message",
        "message": {
            "level": level,
            "message": message,
            "code": {"code": code, "explanation": None} if code else None,
            "spans": [span],
            "children": [],
            "rendered": f"{level}: {message}\n --> {file_name}:{line}:5\n",
        },
    })


def _annotations(stdout: str) -> list[str]:
    return [line for line in stdout.splitlines() if line.startswith("::")]


def test_feedback_script_is_identical_in_every_gate_workflow() -> None:
    assert len({_script(workflow) for workflow in GATES}) == 1


@pytest.mark.parametrize("workflow", GATES)
def test_gates_pipe_cargo_through_the_feedback_script(workflow: str) -> None:
    steps = _steps(workflow)
    gates = [step for step in steps if step.get("id") in GATES[workflow][1]]
    names = [step.get("name") for step in steps]

    assert len(gates) == len(GATES[workflow][1])
    assert names.index("Set up run feedback") < names.index(gates[0]["name"])
    for gate in gates:
        # pipefail keeps cargo's exit status; the script only reports.
        assert "set -euo pipefail" in gate["run"]
        assert '| python "$RUNNER_TEMP/rust_feedback.py" filter' in gate["run"]

    summary = steps[-1]
    assert summary["name"] == "Summary"
    assert summary["if"] == "always()"
    assert summary["env"] == {"STEPS": "${{ toJSON(steps) }}"}
    for step_id in GATES[workflow][1]:
        assert f" {step_id}=" in summary["run"]


@posix_only
def test_filter_annotates_each_compiler_diagnostic_once(tmp_path: Path) -> None:
    """Lib and test builds report the same lint twice; annotate and print it once."""
    lint = _compiler_message(
        "error", "unneeded `return` statement", "clippy::needless_return", "src/lib.rs", 5
    )
    cargo = [
        '{"reason": "compiler-artifact", "package_id": "fixture"}',
        lint,
        lint,
        json.dumps({"reason": "compiler-message", "message": {
            "level": "error", "message": "aborting due to 1 previous error", "code": None,
            "spans": [], "children": [], "rendered": "error: aborting due to 1 previous error\n",
        }}),
        "plain line",
    ]

    proc, outputs = _run_script(tmp_path, "filter", stdin="\n".join(cargo) + "\n")

    assert proc.returncode == 0, proc.stderr
    assert _annotations(proc.stdout) == [
        "::error file=crate/src/lib.rs,line=5,col=5,endLine=5,endColumn=17,"
        "title=clippy%3A%3Aneedless_return::unneeded `return` statement"
    ]
    assert proc.stdout.count("error: unneeded `return` statement") == 1
    assert "aborting due to 1 previous error" in proc.stdout
    assert "plain line" in proc.stdout
    assert "compiler-artifact" not in proc.stdout
    assert outputs["errors"] == "1"
    assert outputs["warnings"] == "0"


@posix_only
def test_filter_escapes_messages_and_follows_macro_expansions(tmp_path: Path) -> None:
    expansion = {"span": {
        "file_name": "src/lib.rs", "line_start": 9, "line_end": 9,
        "column_start": 1, "column_end": 20, "is_primary": True, "expansion": None,
    }}
    cargo = [
        _compiler_message(
            "warning", "50% done\nnext", None, "/rustc/abc/core/macros.rs", 3, expansion
        ),
        _compiler_message("warning", "in a dependency", "unused", "/home/me/.cargo/x.rs", 1),
    ]

    proc, outputs = _run_script(tmp_path, "filter", stdin="\n".join(cargo) + "\n")

    assert _annotations(proc.stdout) == [
        "::warning file=crate/src/lib.rs,line=9,col=1,endLine=9,endColumn=20,"
        "title=rustc::50%25 done%0Anext",
        "::warning title=unused::in a dependency",
    ]
    assert outputs["warnings"] == "2"


@posix_only
def test_filter_annotates_rustfmt_diffs(tmp_path: Path) -> None:
    rustfmt = [
        f"Diff in {tmp_path}/crate/src/lib.rs:3:",
        "-fn a(){}",
        "+fn a() {}",
        f"Diff in {tmp_path}/crate/src/main.rs at line 7:",
    ]

    proc, outputs = _run_script(tmp_path, "filter", stdin="\n".join(rustfmt) + "\n")

    assert _annotations(proc.stdout) == [
        "::error file=crate/src/lib.rs,line=3,title=rustfmt::cargo fmt would reformat this code",
        "::error file=crate/src/main.rs,line=7,title=rustfmt::cargo fmt would reformat this code",
    ]
    assert "+fn a() {}" in proc.stdout
    assert outputs["diffs"] == "2"


@posix_only
@pytest.mark.parametrize("thread_id", ["", " (4242)"])
def test_filter_annotates_failing_tests_and_counts_results(tmp_path: Path, thread_id: str) -> None:
    """Newer toolchains print the thread id after its name in panic messages."""
    libtest = f"""\
running 3 tests
test tests::adds ... FAILED
test tests::skipped ... ignored
test tests::works ... ok

failures:

---- tests::adds stdout ----

thread 'tests::adds'{thread_id} panicked at src/lib.rs:12:9:
assertion `left == right` failed
  left: 4
 right: 5

failures:
    tests::adds

test result: FAILED. 1 passed; 1 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.00s

test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
"""

    proc, outputs = _run_script(tmp_path, "filter", stdin=libtest)

    assert _annotations(proc.stdout) == [
        "::error file=crate/src/lib.rs,line=12,col=9,title=test failed::"
        "tests::adds panicked: assertion `left == right` failed"
    ]
    assert outputs["passed"] == "3"
    assert outputs["failed"] == "1"
    assert outputs["ignored"] == "1"
    assert json.loads(outputs["failed-tests"]) == ["tests::adds"]


def test_summary_tables_every_check(tmp_path: Path) -> None:
    steps = {
        "format": {"outcome": "success", "outputs": {"diffs": "0"}},
        "check": {"outcome": "skipped", "outputs": {}},
        "clippy": {"outcome": "failure", "outputs": {"errors": "2", "warnings": "1"}},
        "tests": {"outcome": "failure", "outputs": {
            "passed": "3", "failed": "1", "ignored": "0", "failed-tests": '["tests::adds"]',
        }},
    }
    summary = tmp_path / "summary.md"

    proc, _ = _run_script(
        tmp_path, "summary", "Rust CI",
        "format=Format", "check=Cargo check", "clippy=Clippy", "tests=Tests", "extra=Extra",
        env={"STEPS": json.dumps(steps), "GITHUB_STEP_SUMMARY": str(summary)},
    )

    assert proc.returncode == 0, proc.stderr
    assert summary.read_text(encoding="utf-8") == """\
## Rust CI

| Check | Result |
| --- | --- |
| Format | ✅ Passed |
| Cargo check | Skipped |
| Clippy | ❌ Failed: 2 errors, 1 warning |
| Tests | ❌ Failed: 3 passed, 1 failed, 0 ignored |
| Extra | Not run |

**Failed tests**

- `tests::adds`
"""


@posix_only
@pytest.mark.parametrize(
    ("workflow", "step", "source", "annotation", "count"),
    [
        ("rust-ci.yml", "Format check", UNFORMATTED_LIB, "title=rustfmt::", "diffs"),
        ("rust-ci.yml", "Cargo check", COMPILE_ERROR_LIB, "title=E0425::", "errors"),
        ("rust-ci.yml", "Clippy", LIB_CLIPPY_WARNING, CLIPPY_RETURN, "errors"),
        ("rust-ci.yml", "Tests", FAILING_TEST_LIB, "title=test failed::tests::adds", "failed"),
        ("rust-quality.yml", "Clippy", LIB_CLIPPY_WARNING, CLIPPY_RETURN, "errors"),
        ("rust-docs.yml", "Build documentation", BROKEN_DOC_LINK_LIB,
         "title=rustdoc%3A%3Abroken_intra_doc_links::", "errors"),
    ],
)
def test_real_cargo_failures_are_annotated_in_the_crate(
    tmp_path: Path, workflow: str, step: str, source: str, annotation: str, count: str
) -> None:
    require_rust_tools("fmt", "clippy")
    crate = write_crate(tmp_path / "crate", source)

    result = run_step(workflow, GATES[workflow][0], step, crate)

    assert result.code != 0, result.stdout + result.stderr
    annotations = _annotations(result.stdout)
    assert any(line.startswith("::error file=crate/src/lib.rs,line=") and annotation in line
               for line in annotations), result.stdout
    assert int(result.outputs[count]) >= 1


@posix_only
def test_summary_step_writes_to_the_job_summary(tmp_path: Path) -> None:
    crate = tmp_path / "crate"
    crate.mkdir()
    steps = {"docs": {"outcome": "success", "outputs": {"errors": "0", "warnings": "0"}}}

    result = run_step(
        "rust-docs.yml", "docs", "Summary", crate, context={"toJSON(steps)": json.dumps(steps)}
    )

    assert result.code == 0, result.stderr
    assert "| Documentation | ✅ Passed |" in result.summary
