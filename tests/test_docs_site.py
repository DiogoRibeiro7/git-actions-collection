from __future__ import annotations

from pathlib import Path
import re

import pytest
import yaml

from scripts import docs_site
from scripts.docs_site import Page

ROOT = Path(__file__).resolve().parents[1]
BLOB = f"{docs_site.REPOSITORY}/blob/main"


def test_every_repository_guide_is_published_once() -> None:
    pages = docs_site.discover_pages(ROOT)
    sources = {page.source for page in pages}
    targets = [page.target for page in pages]

    assert len(targets) == len(set(targets))
    assert set(docs_site.ROOT_PAGES) <= sources
    assert {f"docs/{path.name}" for path in (ROOT / "docs").glob("*.md")} <= sources
    assert "examples/rust-crate/README.md" in sources
    assert ".github/actions/check-imports/README.md" in sources
    # Fixture crates inside an example are packaging inputs, not site pages.
    assert "examples/rust-workspace/crates/cli/README.md" not in sources


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for path in (
        "README.md",
        "CONTRIBUTING.md",
        "docs/guide.md",
        "examples/demo/README.md",
        "examples/other/README.md",
        "examples/demo/diagram.png",
        ".github/workflows/ci.yml",
        "scripts/tool.py",
    ):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("# Title\n", encoding="utf-8")
    return tmp_path


PAGES = {
    page.source: page
    for page in (
        Page("README.md", "index.md", "Home"),
        Page("CONTRIBUTING.md", "contributing.md", "Contributing"),
        Page("docs/guide.md", "guide.md", "Guide"),
        Page("examples/demo/README.md", "examples/demo.md", "demo"),
        Page("examples/other/README.md", "examples/other.md", "other"),
    )
}


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        ("README.md", "https://example.test/x.md", "https://example.test/x.md"),
        ("README.md", "mailto:someone@example.test", "mailto:someone@example.test"),
        ("README.md", "#usage", "#usage"),
        ("README.md", "/absolute.md", "/absolute.md"),
        ("README.md", "docs/guide.md", "guide.md"),
        ("README.md", "CONTRIBUTING.md#run-the-checks", "contributing.md#run-the-checks"),
        ("docs/guide.md", "../CONTRIBUTING.md", "contributing.md"),
        ("docs/guide.md", "../examples/demo/README.md", "examples/demo.md"),
        ("examples/demo/README.md", "../other", "other.md"),
        ("examples/demo/README.md", "../../README.md#status", "../index.md#status"),
        ("README.md", ".github/workflows/ci.yml", f"{BLOB}/.github/workflows/ci.yml"),
        ("docs/guide.md", "../scripts/tool.py#L3", f"{BLOB}/scripts/tool.py#L3"),
        ("README.md", "scripts", f"{docs_site.REPOSITORY}/tree/main/scripts"),
        ("README.md", "missing.md", "missing.md"),
        ("README.md", "../outside.md", "../outside.md"),
    ],
)
def test_links_resolve_to_site_pages_or_github(
    repo: Path, source: str, target: str, expected: str
) -> None:
    assert docs_site.resolve_link(target, PAGES[source], PAGES, repo, image=False) == expected


def test_repository_images_are_served_raw(repo: Path) -> None:
    link = docs_site.resolve_link(
        "diagram.png", PAGES["examples/demo/README.md"], PAGES, repo, image=True
    )

    assert link == f"{docs_site.RAW}/examples/demo/diagram.png"


def test_rewrite_leaves_code_blocks_alone(repo: Path) -> None:
    text = (
        'See [the guide](docs/guide.md "Guide") and ![map](examples/demo/diagram.png).\n'
        "```markdown\n[literal](docs/guide.md)\n```\n"
        "[ref]: CONTRIBUTING.md\n"
    )

    rewritten = docs_site.rewrite_links(text, PAGES["README.md"], PAGES, repo)

    assert '[the guide](guide.md "Guide")' in rewritten
    assert "![map](https://raw.githubusercontent.com/" in rewritten
    assert "[literal](docs/guide.md)" in rewritten
    assert "[ref]: contributing.md" in rewritten


def test_navigation_lists_policy_pages_then_sorted_sections() -> None:
    pages = [
        Page("README.md", "index.md", "Home"),
        Page("SUPPORT.md", "support.md", "Support policy"),
        Page("docs/b.md", "b.md", "Zeta guide"),
        Page("docs/a.md", "a.md", "alpha guide"),
        Page("examples/x/README.md", "examples/x.md", "x"),
        Page(".github/actions/y/README.md", "actions/y.md", "y"),
    ]

    assert docs_site.render_nav(pages).splitlines() == [
        "* [Home](index.md)",
        "* [Support policy](support.md)",
        "* Guides",
        "    * [alpha guide](a.md)",
        "    * [Zeta guide](b.md)",
        "* Examples",
        "    * [x](examples/x.md)",
        "* Composite actions",
        "    * [y](actions/y.md)",
    ]


def _workflow() -> dict:
    return yaml.safe_load((ROOT / ".github/workflows/docs.yml").read_text(encoding="utf-8"))


def test_docs_build_is_read_only_and_deploy_is_gated() -> None:
    workflow = _workflow()
    build, deploy = workflow["jobs"]["build"], workflow["jobs"]["deploy"]
    main_push = "github.event_name != 'pull_request' && github.ref == 'refs/heads/main'"

    assert workflow["permissions"] == {"contents": "read"}
    assert "permissions" not in build
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["if"] == main_push
    upload = next(step for step in build["steps"] if step.get("name") == "Upload Pages artifact")
    assert upload["if"] == main_push


def test_docs_workflow_pins_actions_and_hashes_dependencies() -> None:
    steps = [step for job in _workflow()["jobs"].values() for step in job["steps"]]
    for step in steps:
        if "uses" in step:
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", step["uses"]), step["uses"]
    install = next(step for step in steps if step.get("name") == "Install documentation toolchain")
    assert "--require-hashes -r requirements-docs.txt" in install["run"]


def test_docs_lock_pins_mkdocs_1_with_hashes() -> None:
    lock = (ROOT / "requirements-docs.txt").read_text(encoding="utf-8")
    requirements = re.findall(r"^([a-z0-9._-]+)==(\S+)", lock, re.MULTILINE)
    hashed = re.findall(
        r"^[a-z0-9._-]+==\S+(?: ;[^\\\n]*)? \\\n(?:    --hash=sha256:[0-9a-f]{64}(?: \\)?\n)+",
        lock,
        re.MULTILINE,
    )

    assert ("mkdocs", "1.6.1") in requirements
    assert len(hashed) == len(requirements)


def test_site_build_is_strict() -> None:
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

    assert config["strict"] is True
    assert set(config["validation"].values()) == {"warn"}
    scripts = next(
        plugin for plugin in config["plugins"] if isinstance(plugin, dict) and "gen-files" in plugin
    )
    assert scripts["gen-files"]["scripts"] == ["scripts/docs_site.py"]
