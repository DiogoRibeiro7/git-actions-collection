#!/usr/bin/env python3
"""Intelligent multi-language dependency updater with conflict detection.

Features:
- Parses package manifests (package.json, pyproject.toml, Cargo.toml, go.mod, Gemfile)
- Bumps dependencies to latest patch release (simple heuristic)
- Detects version conflicts and potential breaking changes
- Optional Dependabot alert integration via GitHub API
- Emits JSON report of updates and conflicts
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    import tomlkit  # type: ignore
    from packaging.requirements import Requirement
    from packaging.version import Version
    import requests  # type: ignore
except Exception as exc:  # pragma: no cover - installation handled by composite action
    print(f"Missing dependency: {exc}", file=sys.stderr)
    sys.exit(1)


@dataclass
class UpdateResult:
    name: str
    current: str
    updated: str
    manifest: Path
    breaking: bool

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "current": self.current,
            "updated": self.updated,
            "manifest": str(self.manifest),
            "breaking": self.breaking,
        }


ParsedSemver = Tuple[str, str, str, str, str]
SEMVER_RE = re.compile(
    r"^(?P<leading>\s*)(?P<operator>\^|~|~=|==|!=|>=|<=|>|<|=)?(?P<mid_ws>\s*)(?P<vprefix>v)?"
    r"(?P<core>\d+(?:\.\d+){0,2})(?P<suffix>.*)$"
)
PEP621_SPEC_RE = re.compile(
    r"(?P<token>\s*(?:\^|~|~=|==|!=|>=|<=|>|<|=)\s*v?\d+(?:\.\d+){0,2})"
)


def _split_semver(token: str) -> Tuple[ParsedSemver, str] | None:
    match = SEMVER_RE.match(token)
    if not match:
        return None
    parts: ParsedSemver = (
        match.group("leading") or "",
        match.group("operator") or "",
        match.group("mid_ws") or "",
        match.group("vprefix") or "",
        match.group("core"),
    )
    return parts, match.group("suffix") or ""


def _version_for_compare(token: str) -> Version | None:
    parsed = _split_semver(token)
    if not parsed:
        return None
    (_, _, _, _, core), _suffix = parsed
    try:
        return Version(core)
    except Exception:
        return None


def _is_breaking(old: str, new: str) -> bool:
    old_v = _version_for_compare(old)
    new_v = _version_for_compare(new)
    return bool(old_v and new_v and new_v.major > old_v.major)


def bump_patch(version: str) -> str:
    parsed = _split_semver(version)
    if not parsed:
        return version
    (leading, operator, mid_ws, vprefix, core), suffix = parsed
    try:
        ver = Version(core)
    except Exception:
        return version
    new_core = f"{ver.major}.{ver.minor}.{ver.micro + 1}"
    return f"{leading}{operator}{mid_ws}{vprefix}{new_core}{suffix}"


def parse_package_json(path: Path) -> Dict[str, str]:
    data = json.loads(path.read_text())
    return {**data.get("dependencies", {}), **data.get("devDependencies", {})}


def parse_pyproject(path: Path) -> Dict[str, str]:
    data = tomlkit.parse(path.read_text())
    deps: Dict[str, str] = {}
    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        try:
            req = Requirement(str(dep))
        except Exception:
            continue
        version = str(next(iter(req.specifier))) if req.specifier else "0"
        deps[req.name] = version or "0"
    poetry = data.get("tool", {}).get("poetry", {})
    for name, ver in poetry.get("dependencies", {}).items():
        if name == "python":
            continue
        if hasattr(ver, "get"):
            deps[name] = str(ver.get("version", "0"))
        else:
            deps[name] = str(ver)
    return deps


def parse_cargo(path: Path) -> Dict[str, str]:
    data = tomlkit.parse(path.read_text())
    deps = {}
    for name, val in data.get("dependencies", {}).items():
        if hasattr(val, "get"):
            deps[name] = str(val.get("version", "0"))
        else:
            deps[name] = str(val)
    return deps


def parse_gomod(path: Path) -> Dict[str, str]:
    deps = {}
    line_re = re.compile(r"^\s*([\w\-./]+)\s+(v[0-9].*)$")
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("//", "module", "go ", "require", "replace")):
            continue
        match = line_re.match(line)
        if match:
            deps[match.group(1)] = match.group(2)
    return deps


def parse_gemfile(path: Path) -> Dict[str, str]:
    deps = {}
    for line in path.read_text().splitlines():
        m = re.match(r"\s*gem ['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]", line)
        if m:
            deps[m.group(1)] = m.group(2)
    return deps


PARSERS = {
    "package.json": parse_package_json,
    "pyproject.toml": parse_pyproject,
    "Cargo.toml": parse_cargo,
    "go.mod": parse_gomod,
    "Gemfile": parse_gemfile,
}


def gather_deps(manifests: Iterable[Path]) -> Dict[str, List[Tuple[str, Path]]]:
    all_deps: Dict[str, List[Tuple[str, Path]]] = {}
    for m in manifests:
        parser = PARSERS.get(m.name)
        if not parser:
            continue
        for name, ver in parser(m).items():
            all_deps.setdefault(name, []).append((ver, m))
    return all_deps


def detect_conflicts(deps: Dict[str, List[Tuple[str, Path]]]) -> Dict[str, List[Tuple[str, Path]]]:
    conflicts: Dict[str, List[Tuple[str, Path]]] = {}
    for name, versions in deps.items():
        majors = set()
        for ver, manifest in versions:
            parsed = _version_for_compare(ver)
            if parsed is not None:
                majors.add(parsed.major)
        if len(majors) > 1:
            conflicts[name] = versions
    return conflicts


def _serialise_conflicts(conflicts: Dict[str, List[Tuple[str, Path]]]) -> Dict[str, List[Dict[str, str]]]:
    serialised: Dict[str, List[Dict[str, str]]] = {}
    for name, entries in conflicts.items():
        serialised[name] = [
            {"version": ver, "manifest": str(path)} for ver, path in entries
        ]
    return serialised


def apply_updates(manifests: Iterable[Path], batch: int) -> List[UpdateResult]:
    results: List[UpdateResult] = []
    count = 0
    for m in manifests:
        if count >= batch:
            break
        parser = PARSERS.get(m.name)
        if not parser:
            continue
        if m.name == "package.json":
            data = json.loads(m.read_text())
            updated = False
            for section in ("dependencies", "devDependencies"):
                if section not in data:
                    continue
                for name, ver in list(data[section].items()):
                    if count >= batch:
                        break
                    new_ver = bump_patch(ver)
                    if new_ver != ver:
                        data[section][name] = new_ver
                        results.append(
                            UpdateResult(name, ver, new_ver, m, _is_breaking(ver, new_ver))
                        )
                        count += 1
                        updated = True
                if count >= batch:
                    break
            if updated:
                m.write_text(json.dumps(data, indent=2) + "\n")
        elif m.name == "pyproject.toml":
            data = tomlkit.parse(m.read_text())
            updated = False
            tool = data.get("tool", {})
            poetry = tool.get("poetry", {})
            deps_table = poetry.get("dependencies")
            if deps_table:
                for name, ver in list(deps_table.items()):
                    if count >= batch:
                        break
                    if name == "python":
                        continue
                    value = ver.get("version", "0") if hasattr(ver, "get") else ver
                    ver_str = str(value)
                    new_ver = bump_patch(ver_str)
                    if new_ver != ver_str:
                        if hasattr(ver, "__setitem__") and hasattr(ver, "get"):
                            ver["version"] = new_ver
                        else:
                            deps_table[name] = new_ver
                        results.append(
                            UpdateResult(name, ver_str, new_ver, m, _is_breaking(ver_str, new_ver))
                        )
                        count += 1
                        updated = True
            project = data.get("project")
            if count < batch and project and "dependencies" in project:
                deps_list = project["dependencies"]
                for idx, dep in enumerate(list(deps_list)):
                    if count >= batch:
                        break
                    dep_str = str(dep)
                    match = PEP621_SPEC_RE.search(dep_str)
                    if not match:
                        continue
                    token = match.group("token")
                    new_token = bump_patch(token)
                    if new_token == token:
                        continue
                    try:
                        req = Requirement(dep_str)
                        name = req.name
                    except Exception:
                        continue
                    deps_list[idx] = dep_str[: match.start()] + new_token + dep_str[match.end() :]
                    results.append(
                        UpdateResult(name, token.strip(), new_token.strip(), m, _is_breaking(token, new_token))
                    )
                    count += 1
                    updated = True
            if updated:
                m.write_text(tomlkit.dumps(data))
        elif m.name == "Cargo.toml":
            data = tomlkit.parse(m.read_text())
            updated = False
            deps_table = data.get("dependencies")
            if deps_table:
                for name, ver in list(deps_table.items()):
                    if count >= batch:
                        break
                    value = ver.get("version", "0") if hasattr(ver, "get") else ver
                    ver_str = str(value)
                    new_ver = bump_patch(ver_str)
                    if new_ver != ver_str:
                        if hasattr(ver, "__setitem__") and hasattr(ver, "get"):
                            ver["version"] = new_ver
                        else:
                            deps_table[name] = new_ver
                        results.append(
                            UpdateResult(name, ver_str, new_ver, m, _is_breaking(ver_str, new_ver))
                        )
                        count += 1
                        updated = True
            if updated:
                m.write_text(tomlkit.dumps(data))
        elif m.name == "go.mod":
            lines = m.read_text().splitlines()
            new_lines: List[str] = []
            updated = False
            for line in lines:
                if count >= batch:
                    new_lines.append(line)
                    continue
                mver = re.match(r"(\s*)([\w\-./]+)\s+(v[0-9].*)", line)
                if mver and mver.group(2) not in {"module", "require", "replace"}:
                    prefix, module, ver = mver.groups()
                    new_ver = bump_patch(ver)
                    if new_ver != ver:
                        new_lines.append(f"{prefix}{module} {new_ver}")
                        results.append(
                            UpdateResult(module, ver, new_ver, m, _is_breaking(ver, new_ver))
                        )
                        count += 1
                        updated = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            if updated:
                m.write_text("\n".join(new_lines) + "\n")
        elif m.name == "Gemfile":
            text = m.read_text()
            updated = False

            def repl(match: re.Match[str]) -> str:
                nonlocal count, updated
                if count >= batch:
                    return match.group(0)
                name, ver = match.group(1), match.group(2)
                new_ver = bump_patch(ver)
                if new_ver != ver:
                    results.append(
                        UpdateResult(name, ver, new_ver, m, _is_breaking(ver, new_ver))
                    )
                    count += 1
                    updated = True
                    return f"gem '{name}', '{new_ver}'"
                return match.group(0)

            new_text = re.sub(r"gem ['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]", repl, text)
            if updated:
                m.write_text(new_text)
    return results


def fetch_dependabot_alerts(token: str, repo: str) -> List[dict]:
    url = f"https://api.github.com/repos/{repo}/dependabot/alerts"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", nargs="+", default=[])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--batch-size", type=int, default=50)
    ap.add_argument("--dependabot", action="store_true")
    ap.add_argument("--repo", help="owner/repo for Dependabot API")
    args = ap.parse_args()

    manifests = [Path(m) for m in args.manifests if Path(m).exists()]
    deps = gather_deps(manifests)
    conflicts = detect_conflicts(deps)

    updates: List[UpdateResult] = []
    if args.apply:
        updates = apply_updates(manifests, args.batch_size)

    alerts: List[dict] = []
    if args.dependabot and args.repo and (token := os.environ.get("GITHUB_TOKEN")):
        try:
            alerts = fetch_dependabot_alerts(token, args.repo)
        except Exception as exc:  # pragma: no cover - network failures
            print(f"Failed to fetch Dependabot alerts: {exc}", file=sys.stderr)

    report = {
        "updates": [r.to_dict() for r in updates],
        "conflicts": _serialise_conflicts(conflicts),
        "alerts": alerts,
    }
    print(json.dumps(report))

    # exit non-zero on conflicts for CI visibility
    if conflicts:
        sys.exit(1)


if __name__ == "__main__":
    main()
