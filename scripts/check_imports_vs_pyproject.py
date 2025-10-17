#!/usr/bin/env python3
"""Compare imported packages to dependencies in pyproject.toml.
Usage:
  python scripts/check_imports_vs_pyproject.py --fail-on missing --format text
"""
import argparse, ast, os, sys, json, tomllib, importlib.util, sysconfig
from pathlib import Path

def find_python_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_file() and p.suffix == ".py":
            yield p
        elif p.is_dir():
            for fp in p.rglob("*.py"):
                yield fp

def extract_top_level_imports(pyfile):
    mods = set()
    try:
        tree = ast.parse(pyfile.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return mods
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
    # ignore stdlib by simple heuristic: lowercase, no hyphen, short common modules left in but filtered later if needed
    return mods

def load_pyproject_deps(pyproject_path: Path):
    if not pyproject_path.exists():
        return set()
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8", errors="ignore"))
    deps: set[str] = set()
    project = data.get("project")
    if project:
        for dep in project.get("dependencies", []):
            deps.add(dep.split()[0].replace("_", "-"))
    poetry = data.get("tool", {}).get("poetry")
    if poetry:
        for name in poetry.get("dependencies", {}):
            if name != "python":
                deps.add(name.replace("_", "-"))
    return deps

def write_missing_to_pyproject(missing: list[str]):
    """Append missing dependencies to pyproject.toml if present."""
    import tomlkit

    pyproj = Path("pyproject.toml")
    if not pyproj.exists() or not missing:
        return
    doc = tomlkit.parse(pyproj.read_text())

    if "project" in doc:
        deps = doc["project"].get("dependencies", tomlkit.array())
        for pkg in missing:
            if pkg not in deps:
                deps.append(pkg)
        doc["project"]["dependencies"] = deps
    else:
        tool = doc.setdefault("tool", tomlkit.table())
        poetry = tool.setdefault("poetry", tomlkit.table())
        deps = poetry.get("dependencies", tomlkit.table())
        for pkg in missing:
            if pkg not in deps:
                deps[pkg] = "*"
        poetry["dependencies"] = deps

    pyproj.write_text(tomlkit.dumps(doc))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="+", default=["."])
    ap.add_argument("--fail-on", choices=["missing", "unused", "both", "none"], default="missing")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--update", action="store_true", help="Add missing imports to pyproject.toml")
    args = ap.parse_args()

    files = list(find_python_files(args.paths))
    imports = set()
    for fp in files:
        imports |= extract_top_level_imports(fp)

    # exclude stdlib modules using importlib metadata and ignore local packages
    stdlib_dir = Path(sysconfig.get_paths()["stdlib"])

    def is_stdlib(mod: str) -> bool:
        spec = importlib.util.find_spec(mod)
        if spec is None:
            return False
        if spec.origin in (None, "built-in", "frozen"):
            return True
        try:
            origin = Path(spec.origin)
            origin.relative_to(stdlib_dir)
            return "site-packages" not in origin.parts
        except ValueError:
            return False

    local_modules = {p.name for p in Path(".").glob("*/")}
    imports = {m for m in imports if not is_stdlib(m) and m not in local_modules}

    deps = load_pyproject_deps(Path("pyproject.toml"))
    # normalize names
    norm = lambda s: s.replace("_","-").lower()
    imports_n = {norm(m) for m in imports}
    deps_n = {norm(d) for d in deps}

    missing = sorted(imports_n - deps_n)
    unused = sorted(deps_n - imports_n)

    result = {"missing": missing, "unused": unused}
    if args.format == "json":
        print(json.dumps(result))
    else:
        if missing:
            print("Missing in pyproject:", ", ".join(missing))
        if unused:
            print("Unused in pyproject:", ", ".join(unused))
        if not missing and not unused:
            print("All good: imports match pyproject.")

    if args.update and missing:
        write_missing_to_pyproject(missing)

    exit_code = 0
    if args.fail_on in ("missing","both") and missing and not args.update:
        exit_code = 1
    if args.fail_on in ("unused","both") and unused:
        exit_code = 1 if exit_code == 0 else exit_code
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
