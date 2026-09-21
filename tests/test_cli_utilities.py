import json
import sys
from pathlib import Path

import pytest

import scripts.check_imports_vs_pyproject as check_imports
import scripts.pypi_trusted_publishing_wizard as pypi_wizard
import scripts.pyproject_updater as pyproject_updater
import scripts.workflow_generator as workflow_generator


def test_check_imports_reports_missing_and_unused(tmp_path, monkeypatch, capsys):
    project = tmp_path
    (project / "src").mkdir()
    (project / "src" / "app.py").write_text(
        "import requests\nimport httpx\n", encoding="utf-8"
    )
    (project / "pyproject.toml").write_text(
        """[project]
name = "demo"
dependencies = [
  "requests >=2.0",
  "unused-pkg >=1.0",
]
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(project)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check", "--paths", "src", "--format", "json", "--fail-on", "none"],
    )

    with pytest.raises(SystemExit) as exc:
        check_imports.main()
    assert exc.value.code == 0

    payload = json.loads(capsys.readouterr().out)
    assert "httpx" in payload["missing"]
    assert "unused-pkg" in payload["unused"]


def test_check_imports_update_adds_missing(tmp_path, monkeypatch):
    project = tmp_path
    (project / "src").mkdir()
    (project / "src" / "app.py").write_text("import requests\n", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        """[project]
name = "demo"
dependencies = []
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(project)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check", "--paths", "src", "--format", "text", "--update", "--fail-on", "none"],
    )

    with pytest.raises(SystemExit) as exc:
        check_imports.main()
    assert exc.value.code == 0

    updated = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "requests" in updated


def test_pyproject_updater_updates_pep621_deps(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "demo"
dependencies = [
  "requests >=1.0",
  "flask >=2.0",
]
""",
        encoding="utf-8",
    )

    class FakeResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        def read(self) -> bytes:
            return json.dumps(self._data).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url, timeout=0):
        if "requests" in url:
            data = {
                "releases": {
                    "2.1.0": [{"yanked": False}],
                    "3.0.0rc1": [{"yanked": False}],
                    "2.1.1": [{"yanked": True}],
                }
            }
        else:
            data = {
                "releases": {
                    "2.2.5": [{"yanked": False}],
                    "3.0.0rc1": [{"yanked": False}],
                }
            }
        return FakeResponse(data)

    monkeypatch.setattr(pyproject_updater.urllib.request, "urlopen", fake_urlopen)

    opts = pyproject_updater.Options(
        strategy="caret",
        allow_major=False,
        include_prerelease=False,
        groups=["main"],
        only=None,
        check=False,
        file=pyproject,
        timeout=1.0,
    )

    result = pyproject_updater.upgrade(pyproject, opts)
    assert result == 0

    text = pyproject.read_text(encoding="utf-8")
    assert "requests >=2.1.0,<3.0.0" in text
    assert "flask >=2.2.5,<3.0.0" in text


def test_pyproject_updater_allows_major_and_prerelease(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "demo"
dependencies = [
  "requests >=2.0",
]
""",
        encoding="utf-8",
    )

    class FakeResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        def read(self) -> bytes:
            return json.dumps(self._data).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url, timeout=0):
        data = {"releases": {"2.5.0": [{"yanked": False}], "3.0.0rc1": [{"yanked": False}]}}
        return FakeResponse(data)

    monkeypatch.setattr(pyproject_updater.urllib.request, "urlopen", fake_urlopen)

    opts = pyproject_updater.Options(
        strategy="exact",
        allow_major=True,
        include_prerelease=True,
        groups=["main"],
        only=None,
        check=False,
        file=pyproject,
        timeout=1.0,
    )

    result = pyproject_updater.upgrade(pyproject, opts)
    assert result == 0

    text = pyproject.read_text(encoding="utf-8")
    assert "requests ==3.0.0rc1" in text


def test_pyproject_updater_check_mode_outputs_diff(tmp_path, monkeypatch, capsys):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "demo"
dependencies = [
  "requests >=1.0",
]
""",
        encoding="utf-8",
    )

    class FakeResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        def read(self) -> bytes:
            return json.dumps(self._data).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url, timeout=0):
        data = {"releases": {"2.0.1": [{"yanked": False}]}}
        return FakeResponse(data)

    monkeypatch.setattr(pyproject_updater.urllib.request, "urlopen", fake_urlopen)

    opts = pyproject_updater.Options(
        strategy="floor",
        allow_major=False,
        include_prerelease=False,
        groups=["main"],
        only=None,
        check=True,
        file=pyproject,
        timeout=1.0,
    )

    result = pyproject_updater.upgrade(pyproject, opts)
    assert result == 0

    original = pyproject.read_text(encoding="utf-8")
    assert '"requests >=1.0"' in original
    diff = capsys.readouterr().out
    assert diff.startswith("--- ")
    assert "+  \"requests >=2.0.1\"" in diff
    assert "+[project.optional-dependencies]" in diff


def test_pyproject_updater_updates_poetry_deps(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.poetry]
name = "demo"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.12"
requests = "^2.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
""",
        encoding="utf-8",
    )

    class FakeResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        def read(self) -> bytes:
            return json.dumps(self._data).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url, timeout=0):
        if "requests" in url:
            data = {"releases": {"2.1.0": [{"yanked": False}]}}
        else:
            data = {"releases": {"7.4.0": [{"yanked": False}]}}
        return FakeResponse(data)

    monkeypatch.setattr(pyproject_updater.urllib.request, "urlopen", fake_urlopen)

    opts = pyproject_updater.Options(
        strategy="caret",
        allow_major=False,
        include_prerelease=False,
        groups=["main", "dev"],
        only=None,
        check=False,
        file=pyproject,
        timeout=1.0,
    )

    result = pyproject_updater.upgrade(pyproject, opts)
    assert result == 0

    text = pyproject.read_text(encoding="utf-8")
    assert 'requests = "^2.1.0"' in text
    assert 'pytest = "^7.4.0"' in text


def test_pyproject_updater_only_filter(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "demo"
dependencies = [
  "requests >=1.0",
  "flask >=1.0",
]
""",
        encoding="utf-8",
    )

    class FakeResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        def read(self) -> bytes:
            return json.dumps(self._data).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url, timeout=0):
        if "requests" in url:
            data = {"releases": {"2.0.0": [{"yanked": False}]}}
        else:
            data = {"releases": {"3.0.0": [{"yanked": False}]}}
        return FakeResponse(data)

    monkeypatch.setattr(pyproject_updater.urllib.request, "urlopen", fake_urlopen)

    opts = pyproject_updater.Options(
        strategy="floor",
        allow_major=False,
        include_prerelease=False,
        groups=["main"],
        only=["requests"],
        check=False,
        file=pyproject,
        timeout=1.0,
    )

    result = pyproject_updater.upgrade(pyproject, opts)
    assert result == 0

    text = pyproject.read_text(encoding="utf-8")
    assert "requests >=2.0.0" in text
    assert "flask >=1.0" in text


def test_pyproject_updater_respect_major_picks_within_major(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.poetry]
name = "demo"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.12"
requests = "^2.0"
""",
        encoding="utf-8",
    )

    class FakeResponse:
        def __init__(self, data: dict) -> None:
            self._data = data

        def read(self) -> bytes:
            return json.dumps(self._data).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url, timeout=0):
        data = {
            "releases": {
                "2.9.0": [{"yanked": False}],
                "3.1.0": [{"yanked": False}],
            }
        }
        return FakeResponse(data)

    monkeypatch.setattr(pyproject_updater.urllib.request, "urlopen", fake_urlopen)

    opts = pyproject_updater.Options(
        strategy="floor",
        allow_major=False,
        include_prerelease=False,
        groups=["main"],
        only=None,
        check=False,
        file=pyproject,
        timeout=1.0,
    )

    result = pyproject_updater.upgrade(pyproject, opts)
    assert result == 0

    text = pyproject.read_text(encoding="utf-8")
    assert 'requests = ">=2.9.0"' in text
    assert "3.1.0" not in text


def test_pypi_wizard_creates_workflow(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pypi_wizard.shutil, "which", lambda _: "gh")
    monkeypatch.setattr(
        pypi_wizard.subprocess,
        "check_output",
        lambda *args, **kwargs: "acme/demo\n",
    )
    inputs = iter(["demo-project"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    pypi_wizard.main()

    workflow = tmp_path / ".github" / "workflows" / "publish-to-pypi.yml"
    assert workflow.exists()
    assert "publish-to-pypi.yml@main" in workflow.read_text(encoding="utf-8")
    expected_path = str(Path(".github") / "workflows" / "publish-to-pypi.yml")
    assert f"Created {expected_path}" in capsys.readouterr().out


def test_pypi_wizard_aborts_on_existing_workflow(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pypi_wizard.shutil, "which", lambda _: "gh")
    monkeypatch.setattr(
        pypi_wizard.subprocess,
        "check_output",
        lambda *args, **kwargs: "acme/demo\n",
    )
    workflow = tmp_path / ".github" / "workflows" / "publish-to-pypi.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("existing", encoding="utf-8")

    inputs = iter(["demo-project", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    pypi_wizard.main()

    assert workflow.read_text(encoding="utf-8") == "existing"
    assert "Aborted - existing workflow preserved." in capsys.readouterr().out


def test_workflow_generator_writes_python_ci(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["workflow-generator", "python", "--branch", "develop"],
    )

    exit_code = workflow_generator.main()
    assert exit_code == 0

    workflow = tmp_path / ".github" / "workflows" / "python-ci.yml"
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "branches: [develop]" in text
    assert f"actions/checkout@{workflow_generator.CHECKOUT_REF}" in text
    assert "workflow written to" in capsys.readouterr().out


def test_workflow_generator_errors_if_exists(tmp_path, monkeypatch):
    target = tmp_path / ".github" / "workflows" / "python-ci.yml"
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["workflow-generator", "python"])
    with pytest.raises(SystemExit):
        workflow_generator.main()