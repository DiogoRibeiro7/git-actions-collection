"""The distribution must contain every module its console scripts import.

`where = ["scripts"]` made setuptools look for the `scripts` package inside itself,
so the wheel held no modules and every console script failed with
ModuleNotFoundError after `pip install`. setuptools is not a test dependency, so
this checks the discovery rules directly on the tracked files.
"""

from __future__ import annotations

import ast
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CONFIG = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _tracked(pattern: str) -> list[PurePosixPath]:
    output = subprocess.run(
        ["git", "ls-files", pattern], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return [PurePosixPath(line) for line in output.splitlines()]


def _packages() -> set[str]:
    """Packages `setuptools.find_packages` returns for the configured `where` and `include`."""
    find = CONFIG["tool"]["setuptools"]["packages"]["find"]
    inits = {path.parent for path in _tracked("**__init__.py")}
    found = set()
    for where in find.get("where", ["."]):
        base = PurePosixPath(where)
        for directory in inits:
            if base != PurePosixPath(".") and base not in directory.parents:
                continue
            parts = directory.relative_to(base).parts
            # find_packages only descends through packages, so every parent needs one too.
            chain = [base.joinpath(*parts[:depth]) for depth in range(1, len(parts) + 1)]
            name = ".".join(parts)
            if parts and all(link in inits for link in chain) and any(
                fnmatch(name, pattern) for pattern in find.get("include", ["*"])
            ):
                found.add(name)
    return found


def test_every_script_module_is_in_a_packaged_package() -> None:
    packages = _packages()
    missing = sorted(
        str(path)
        for path in _tracked("scripts/**.py")
        if ".".join(path.parent.parts) not in packages
    )

    assert "scripts" in packages
    assert not missing, f"modules the wheel would leave out: {missing}"


def test_console_scripts_point_at_packaged_functions() -> None:
    packages = _packages()
    for name, target in CONFIG["project"]["scripts"].items():
        module, function = target.split(":")
        path = ROOT.joinpath(*module.split(".")).with_suffix(".py")
        assert module.rsplit(".", 1)[0] in packages, f"{name}: {module} is not packaged"
        assert path.is_file(), f"{name}: {path} does not exist"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert any(
            isinstance(node, ast.FunctionDef) and node.name == function for node in tree.body
        ), f"{name}: {module} has no function {function}"
